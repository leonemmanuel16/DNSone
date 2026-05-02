"""Schemas para configuración runtime."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class BindSettingsRead(BaseModel):
    """
    Configuración BIND tal como se devuelve al cliente.

    El token NUNCA se devuelve en claro: solo un flag booleano que indica si
    está configurado, y los últimos 4 caracteres como hint visual.
    """

    bind_base_url: str | None
    bind_api_token_set: bool
    bind_api_token_hint: str | None  # ej. "***abcd" — últimos 4 caracteres
    bind_use_mock: bool
    bind_timeout_seconds: int
    bind_max_retries: int


class BindSettingsUpdate(BaseModel):
    """
    Actualización parcial de configuración BIND.

    Convención del token:
    - `None` (campo no enviado) → no modificar
    - `""` (cadena vacía) → borrar el token actual
    - cualquier otro valor → reemplazar el token
    """

    bind_base_url: str | None = None
    bind_api_token: str | None = None
    bind_use_mock: bool | None = None
    bind_timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    bind_max_retries: int | None = Field(default=None, ge=0, le=10)


class CommercialSettingsRead(BaseModel):
    """Reglas comerciales por defecto."""

    default_currency: str
    default_exchange_rate_usd_mxn: Decimal
    default_tax_pct: Decimal


class CommercialSettingsUpdate(BaseModel):
    default_currency: str | None = None
    default_exchange_rate_usd_mxn: Decimal | None = Field(default=None, gt=0)
    default_tax_pct: Decimal | None = Field(default=None, ge=0, le=100)
