"""
Configuración runtime-editable.

Este modelo guarda settings que el usuario puede cambiar **desde la UI** sin
reiniciar la app: credenciales BIND, modo mock, valores comerciales por defecto.

Es una tabla singleton (siempre id=1). Si la fila no existe, las funciones que
leen de aquí caen en valores de `app.core.config.settings` (env vars).
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin


class AppSetting(Base, TimestampMixin):
    """Configuración runtime de la app (singleton, id=1)."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ---- BIND ----
    bind_base_url: Mapped[str | None] = mapped_column(String(255))
    bind_api_token: Mapped[str | None] = mapped_column(String(500))  # plano (MVP)
    bind_use_mock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bind_timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    bind_max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # ---- Reglas comerciales ----
    default_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    default_exchange_rate_usd_mxn: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("19.00"), nullable=False
    )
    default_tax_pct: Mapped[Decimal] = mapped_column(
        Numeric(7, 4), default=Decimal("16.00"), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AppSetting id={self.id} bind_use_mock={self.bind_use_mock}>"
