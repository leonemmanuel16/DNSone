"""Endpoints de sincronización con BIND y bitácora."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permission
from app.core.db import get_db
from app.models.integration import BindSyncLog
from app.models.user import User
from app.schemas.common import Page
from app.schemas.integration import BindSyncLogRead

router = APIRouter()


@router.post("/products", response_model=BindSyncLogRead)
def trigger_sync_products(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("sync.run")),
) -> BindSyncLog:
    """Dispara manualmente el sync de productos desde BIND (no espera al scheduler)."""
    from app.integrations.bind.bind_sync_service import sync_products_from_bind

    log = sync_products_from_bind(db_session=db, manual=True)
    return log


@router.post("/quote-status", response_model=BindSyncLogRead)
def trigger_sync_quote_status(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("sync.run")),
) -> BindSyncLog:
    """Dispara manualmente el sync de estatus de cotizaciones."""
    from app.integrations.bind.bind_sync_service import sync_quote_status_from_bind

    log = sync_quote_status_from_bind(db_session=db, manual=True)
    return log


@router.get("/logs", response_model=Page[BindSyncLogRead])
def list_sync_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Page[BindSyncLogRead]:
    stmt = select(BindSyncLog).order_by(BindSyncLog.started_at.desc())
    total = len(db.execute(select(BindSyncLog.id)).all())
    rows = (
        db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return Page[BindSyncLogRead](
        items=[BindSyncLogRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
