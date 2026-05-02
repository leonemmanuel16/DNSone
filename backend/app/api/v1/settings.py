"""
Endpoints de configuración runtime.

- GET    /api/v1/settings/bind          — devuelve config (token enmascarado)
- PATCH  /api/v1/settings/bind          — actualiza config; permiso settings.write
- POST   /api/v1/settings/bind/test     — verifica conectividad con BIND
- GET    /api/v1/settings/commercial    — moneda default, TC, IVA default
- PATCH  /api/v1/settings/commercial    — actualiza
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.api.deps.auth import require_permission
from app.core.db import get_db
from app.core.exceptions import IntegrationError, NotFoundError
from app.models.app_setting import AppSetting
from app.models.user import User
from app.schemas.settings import (
    BindSettingsRead,
    BindSettingsUpdate,
    CommercialSettingsRead,
    CommercialSettingsUpdate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_or_create(db: Session) -> AppSetting:
    """Devuelve el singleton (id=1). Si no existe, lo crea con defaults."""
    row = db.get(AppSetting, 1)
    if row is None:
        row = AppSetting(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _to_bind_read(row: AppSetting) -> BindSettingsRead:
    token = row.bind_api_token or ""
    return BindSettingsRead(
        bind_base_url=row.bind_base_url,
        bind_api_token_set=bool(token),
        bind_api_token_hint=("***" + token[-4:]) if len(token) >= 4 else None,
        bind_use_mock=row.bind_use_mock,
        bind_timeout_seconds=row.bind_timeout_seconds,
        bind_max_retries=row.bind_max_retries,
    )


# ---------------------------------------------------------------------------
# BIND settings
# ---------------------------------------------------------------------------
@router.get("/bind", response_model=BindSettingsRead)
def get_bind_settings(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("settings.read")),
) -> BindSettingsRead:
    return _to_bind_read(_get_or_create(db))


@router.patch("/bind", response_model=BindSettingsRead)
def update_bind_settings(
    body: BindSettingsUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("settings.write")),
) -> BindSettingsRead:
    row = _get_or_create(db)

    if body.bind_base_url is not None:
        row.bind_base_url = body.bind_base_url.strip() or None
    if body.bind_api_token is not None:
        # "" => borrar; cualquier otro valor => reemplazar
        row.bind_api_token = body.bind_api_token.strip() or None
    if body.bind_use_mock is not None:
        row.bind_use_mock = body.bind_use_mock
    if body.bind_timeout_seconds is not None:
        row.bind_timeout_seconds = body.bind_timeout_seconds
    if body.bind_max_retries is not None:
        row.bind_max_retries = body.bind_max_retries

    db.commit()
    db.refresh(row)
    return _to_bind_read(row)


@router.post("/bind/test")
def test_bind_connection(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("settings.write")),
) -> dict:
    """
    Prueba la conectividad con BIND con la configuración guardada.

    Si está en modo mock, simplemente confirma que el modo mock responde.
    Si está en modo real, hace una llamada `get_products` y reporta el resultado.
    """
    from app.integrations.bind.bind_client import get_bind_client

    try:
        client = get_bind_client(db)
        products = client.get_products()
        return {
            "ok": True,
            "use_mock": client.use_mock,
            "products_received": len(products),
            "message": "Conexión OK" + (" (modo mock)" if client.use_mock else ""),
        }
    except IntegrationError as e:
        return {
            "ok": False,
            "error_code": e.code,
            "message": e.message,
            "details": e.details,
        }


# ---------------------------------------------------------------------------
# Commercial settings
# ---------------------------------------------------------------------------
@router.get("/commercial", response_model=CommercialSettingsRead)
def get_commercial_settings(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("settings.read")),
) -> CommercialSettingsRead:
    row = _get_or_create(db)
    return CommercialSettingsRead(
        default_currency=row.default_currency,
        default_exchange_rate_usd_mxn=row.default_exchange_rate_usd_mxn,
        default_tax_pct=row.default_tax_pct,
    )


@router.patch("/commercial", response_model=CommercialSettingsRead)
def update_commercial_settings(
    body: CommercialSettingsUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("settings.write")),
) -> CommercialSettingsRead:
    row = _get_or_create(db)

    if body.default_currency is not None:
        if body.default_currency not in ("USD", "MXN"):
            from app.core.exceptions import ValidationError
            raise ValidationError("default_currency debe ser USD o MXN")
        row.default_currency = body.default_currency
    if body.default_exchange_rate_usd_mxn is not None:
        row.default_exchange_rate_usd_mxn = body.default_exchange_rate_usd_mxn
    if body.default_tax_pct is not None:
        row.default_tax_pct = body.default_tax_pct

    db.commit()
    db.refresh(row)
    return CommercialSettingsRead(
        default_currency=row.default_currency,
        default_exchange_rate_usd_mxn=row.default_exchange_rate_usd_mxn,
        default_tax_pct=row.default_tax_pct,
    )
