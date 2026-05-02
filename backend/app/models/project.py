"""
Modelos de proyecto-cotización.

- `Project`: la cotización como proyecto (cabecera).
- `ProjectVersion`: snapshot inmutable de la cotización en cada push o cambio mayor.
- `QuoteItem`: partidas de la cotización.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin
from app.models.enums import Currency, ProjectStatus


class Project(Base, TimestampMixin):
    """
    Cabecera de la cotización (= proyecto).

    Los totales (`subtotal_*`, `tax_total`, `grand_total`, `margin_pct`) se
    almacenan persistidos pero deben recalcularse vía
    `app.services.pricing.recalculate_project()` cuando cambian las partidas.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identidad
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Cliente
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer = relationship("Customer", lazy="joined")

    # Estado
    status: Mapped[ProjectStatus] = mapped_column(
        String(20), default=ProjectStatus.DRAFT, nullable=False, index=True
    )
    valid_until: Mapped[date | None] = mapped_column(Date)

    # Moneda y FX
    currency: Mapped[Currency] = mapped_column(String(3), default=Currency.USD, nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("19.00"), nullable=False
    )

    # ---- Totales (persistidos por performance, fuente de verdad = recálculo) ----
    subtotal_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    subtotal_sale: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    margin_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"))

    # ---- Integración BIND ----
    bind_quote_id: Mapped[str | None] = mapped_column(String(100), index=True)
    bind_folio: Mapped[str | None] = mapped_column(String(80), index=True)
    bind_status: Mapped[str | None] = mapped_column(String(50))
    bind_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ---- Auditoría ----
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relaciones
    items: Mapped[list["QuoteItem"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="QuoteItem.position",
        lazy="selectin",
    )
    versions: Mapped[list["ProjectVersion"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectVersion.version_number.desc()",
    )

    def __repr__(self) -> str:
        return f"<Project {self.code} status={self.status}>"


class QuoteItem(Base, TimestampMixin):
    """Partida (línea) de la cotización."""

    __tablename__ = "quote_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project: Mapped["Project"] = relationship(back_populates="items")

    # Producto (puede ser ad-hoc, sin FK)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        index=True,
    )

    position: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    qty: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)

    discount_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"))
    tax_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("16"))

    # Calculados (persistidos por reporting; fuente de verdad = recálculo)
    line_cost_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    line_sale_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    line_margin_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"))

    def __repr__(self) -> str:
        return f"<QuoteItem {self.sku} qty={self.qty}>"


class ProjectVersion(Base, TimestampMixin):
    """
    Snapshot inmutable de la cotización.

    Se crea automáticamente al pushear a BIND y manualmente cuando el usuario
    quiere conservar un punto de regreso.
    """

    __tablename__ = "project_versions"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project: Mapped["Project"] = relationship(back_populates="versions")

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(500))

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    def __repr__(self) -> str:
        return f"<ProjectVersion project={self.project_id} v={self.version_number}>"
