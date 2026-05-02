"""Modelo de cliente."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin


class Customer(Base, TimestampMixin):
    """Cliente comercial. Sincronizable con Bind ERP."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identificadores comerciales
    code: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tax_id: Mapped[str | None] = mapped_column(String(20), index=True)  # RFC en MX

    # Contacto
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    contact_name: Mapped[str | None] = mapped_column(String(255))

    # Direcciones (texto plano por ahora; estructurar en fase 2)
    billing_address: Mapped[str | None] = mapped_column(String(500))
    shipping_address: Mapped[str | None] = mapped_column(String(500))

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ---- Integración BIND ----
    bind_customer_id: Mapped[str | None] = mapped_column(String(100), index=True)
    bind_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Customer {self.code} {self.name}>"
