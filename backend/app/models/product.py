"""Modelo de producto / catálogo."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin
from app.models.enums import Currency


class Product(Base, TimestampMixin):
    """
    Producto del catálogo.

    Almacena precios y costos en USD y MXN para evitar conversiones repetidas
    en cotizaciones. La fuente de verdad es BIND vía sync.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identidad
    sku: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Clasificación
    brand: Mapped[str | None] = mapped_column(String(120), index=True)
    category: Mapped[str | None] = mapped_column(String(120), index=True)
    unit: Mapped[str] = mapped_column(String(20), default="PZA", nullable=False)

    # Costos / Precios — Numeric(precision, scale) para precisión decimal
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    cost_mxn: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    list_price_usd: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    list_price_mxn: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))

    currency_default: Mapped[Currency] = mapped_column(
        String(3), default=Currency.USD, nullable=False
    )

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ---- Integración BIND ----
    bind_product_id: Mapped[str | None] = mapped_column(String(100), index=True)
    bind_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Product {self.sku} {self.name}>"
