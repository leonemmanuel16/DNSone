"""
Servicio de sincronización con Bind ERP.

Tres flujos principales:

1. `sync_products_from_bind`: trae catálogo de productos y hace upsert local.
2. `sync_quote_status_from_bind`: actualiza estatus BIND de cotizaciones enviadas.
3. `push_quote_to_bind`: envía una cotización local a Bind y guarda
   `bind_quote_id`, `bind_folio`, `bind_status`.

Cada flujo crea un registro en `bind_sync_logs` (o `integration_events` para
push individual) y maneja errores sin tirar la app.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.exceptions import IntegrationError
from app.integrations.bind.bind_client import get_bind_client
from app.integrations.bind.bind_mapper import bind_to_product_kwargs, project_to_bind_quote
from app.models.enums import (
    BindSyncRunType,
    BindSyncStatus,
    IntegrationEventStatus,
    IntegrationProvider,
)
from app.models.integration import BindSyncLog, IntegrationEvent
from app.models.product import Product
from app.models.project import Project, ProjectVersion

logger = logging.getLogger(__name__)


def _get_session(provided: Session | None) -> tuple[Session, bool]:
    if provided is not None:
        return provided, False
    return SessionLocal(), True


# ---------------------------------------------------------------------------
# 1) Sync productos
# ---------------------------------------------------------------------------
def sync_products_from_bind(
    *, db_session: Session | None = None, manual: bool = False
) -> BindSyncLog:
    db, owned = _get_session(db_session)

    log = BindSyncLog(
        run_type=BindSyncRunType.MANUAL if manual else BindSyncRunType.PRODUCTS,
        status=BindSyncStatus.RUNNING,
        started_at=datetime.now(tz=timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        client = get_bind_client(db)
        products_in = client.get_products()

        log.records_in = len(products_in)
        created = 0
        updated = 0

        for raw in products_in:
            try:
                kwargs = bind_to_product_kwargs(raw)
            except KeyError as e:
                log.errors_count += 1
                logger.warning("Producto BIND sin campo requerido: %s — payload=%s", e, raw)
                continue

            existing = db.execute(
                select(Product).where(Product.bind_product_id == kwargs["bind_product_id"])
            ).scalar_one_or_none()

            now = datetime.now(tz=timezone.utc)
            if existing:
                for k, v in kwargs.items():
                    setattr(existing, k, v)
                existing.bind_synced_at = now
                updated += 1
            else:
                p = Product(**kwargs)
                p.bind_synced_at = now
                db.add(p)
                created += 1

        log.records_out = created + updated
        log.status = (
            BindSyncStatus.SUCCESS if log.errors_count == 0 else BindSyncStatus.PARTIAL
        )
        log.message = f"created={created} updated={updated} errors={log.errors_count}"
        log.ended_at = datetime.now(tz=timezone.utc)
        db.commit()
        logger.info("sync_products_from_bind: %s", log.message)

    except IntegrationError as e:
        log.status = BindSyncStatus.ERROR
        log.message = f"IntegrationError: {e.message}"
        log.ended_at = datetime.now(tz=timezone.utc)
        db.commit()
        logger.exception("sync_products_from_bind falló")
    except Exception as e:
        log.status = BindSyncStatus.ERROR
        log.message = f"Unexpected: {e}"
        log.ended_at = datetime.now(tz=timezone.utc)
        db.commit()
        logger.exception("sync_products_from_bind: error inesperado")
    finally:
        if owned:
            db.close()

    return log


# ---------------------------------------------------------------------------
# 2) Sync estatus de cotizaciones enviadas
# ---------------------------------------------------------------------------
def sync_quote_status_from_bind(
    *, db_session: Session | None = None, manual: bool = False
) -> BindSyncLog:
    db, owned = _get_session(db_session)

    log = BindSyncLog(
        run_type=BindSyncRunType.QUOTES_STATUS,
        status=BindSyncStatus.RUNNING,
        started_at=datetime.now(tz=timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        client = get_bind_client(db)
        projects = (
            db.execute(select(Project).where(Project.bind_quote_id.is_not(None)))
            .scalars()
            .all()
        )
        log.records_in = len(projects)
        updated = 0

        for project in projects:
            try:
                resp = client.get_quote_status(project.bind_quote_id)
                project.bind_status = resp.get("status")
                project.bind_synced_at = datetime.now(tz=timezone.utc)
                updated += 1
            except IntegrationError:
                log.errors_count += 1
                logger.warning("No se pudo actualizar estatus de %s", project.code)

        log.records_out = updated
        log.status = (
            BindSyncStatus.SUCCESS if log.errors_count == 0 else BindSyncStatus.PARTIAL
        )
        log.message = f"updated={updated} errors={log.errors_count}"
        log.ended_at = datetime.now(tz=timezone.utc)
        db.commit()
        logger.info("sync_quote_status_from_bind: %s", log.message)

    except Exception as e:
        log.status = BindSyncStatus.ERROR
        log.message = f"Unexpected: {e}"
        log.ended_at = datetime.now(tz=timezone.utc)
        db.commit()
        logger.exception("sync_quote_status_from_bind falló")
    finally:
        if owned:
            db.close()

    return log


# ---------------------------------------------------------------------------
# 3) Push individual: enviar cotización a BIND
# ---------------------------------------------------------------------------
def push_quote_to_bind(
    db: Session,
    *,
    project: Project,
    user_id: int | None = None,
) -> Project:
    payload = project_to_bind_quote(project)

    event = IntegrationEvent(
        provider=IntegrationProvider.BIND,
        event_type="quote.create",
        status=IntegrationEventStatus.PENDING,
        payload_json=payload,
        project_id=project.id,
    )
    db.add(event)
    db.flush()

    try:
        client = get_bind_client(db)
        resp = client.create_quote(payload)

        project.bind_quote_id = resp.get("bind_quote_id")
        project.bind_folio = resp.get("folio")
        project.bind_status = resp.get("status", "enviada")
        project.bind_synced_at = datetime.now(tz=timezone.utc)

        last_version = (
            db.execute(
                select(ProjectVersion.version_number)
                .where(ProjectVersion.project_id == project.id)
                .order_by(ProjectVersion.version_number.desc())
                .limit(1)
            )
            .scalar_one_or_none()
        )
        version_number = (last_version or 0) + 1
        snapshot = {
            "project": {
                "code": project.code,
                "name": project.name,
                "subtotal_sale": str(project.subtotal_sale),
                "grand_total": str(project.grand_total),
                "currency": str(project.currency),
                "bind_quote_id": project.bind_quote_id,
                "bind_folio": project.bind_folio,
            },
            "items": [
                {
                    "sku": it.sku,
                    "description": it.description,
                    "qty": str(it.qty),
                    "unit_price": str(it.unit_price),
                    "line_sale_total": str(it.line_sale_total),
                }
                for it in project.items
            ],
            "bind_response": resp,
        }
        db.add(
            ProjectVersion(
                project_id=project.id,
                version_number=version_number,
                snapshot_json=snapshot,
                change_note=f"Push a BIND v{version_number}",
                created_by_id=user_id,
            )
        )

        event.status = IntegrationEventStatus.SUCCESS
        event.result_json = resp
        event.completed_at = datetime.now(tz=timezone.utc)
        logger.info(
            "push_quote_to_bind OK project=%s bind_id=%s folio=%s",
            project.code, project.bind_quote_id, project.bind_folio,
        )

    except IntegrationError as e:
        event.status = IntegrationEventStatus.ERROR
        event.error_message = e.message
        event.completed_at = datetime.now(tz=timezone.utc)
        logger.exception("push_quote_to_bind falló")
        raise

    return project
