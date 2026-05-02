"""Schemas de proyecto-cotización y partidas."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Currency, ProjectStatus
from app.schemas.common import ORMModel
from app.schemas.customer import CustomerRead


# ---------------------------------------------------------------------------
# Quote Items
# ---------------------------------------------------------------------------
class QuoteItemBase(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1)
    qty: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal = Field(ge=0)
    discount_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_pct: Decimal = Field(default=Decimal("16"), ge=0, le=100)
    position: int = 1
    product_id: int | None = None


class QuoteItemCreate(QuoteItemBase):
    pass


class QuoteItemUpdate(BaseModel):
    sku: str | None = None
    description: str | None = None
    qty: Decimal | None = None
    unit_cost: Decimal | None = None
    unit_price: Decimal | None = None
    discount_pct: Decimal | None = None
    tax_pct: Decimal | None = None
    position: int | None = None


class QuoteItemRead(ORMModel, QuoteItemBase):
    id: int
    project_id: int
    line_cost_total: Decimal
    line_sale_total: Decimal
    line_margin_pct: Decimal


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------
class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    notes: str | None = None
    customer_id: int
    currency: Currency = Currency.USD
    exchange_rate: Decimal = Field(default=Decimal("19.00"), gt=0)
    discount_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    valid_until: date | None = None


class ProjectCreate(ProjectBase):
    items: list[QuoteItemCreate] = []


class ProjectUpdate(BaseModel):
    name: str | None = None
    notes: str | None = None
    customer_id: int | None = None
    currency: Currency | None = None
    exchange_rate: Decimal | None = None
    discount_pct: Decimal | None = None
    valid_until: date | None = None
    status: ProjectStatus | None = None


class ProjectTotals(BaseModel):
    """Resultado del recálculo, sin modelos ORM."""

    model_config = ConfigDict(from_attributes=True)

    subtotal_cost: Decimal
    subtotal_sale: Decimal
    discount_amount: Decimal
    tax_total: Decimal
    grand_total: Decimal
    margin_pct: Decimal


class ProjectRead(ORMModel):
    id: int
    code: str
    name: str
    notes: str | None = None
    customer_id: int
    customer: CustomerRead | None = None
    status: ProjectStatus
    currency: Currency
    exchange_rate: Decimal
    valid_until: date | None = None

    subtotal_cost: Decimal
    subtotal_sale: Decimal
    discount_pct: Decimal
    discount_amount: Decimal
    tax_total: Decimal
    grand_total: Decimal
    margin_pct: Decimal

    bind_quote_id: str | None = None
    bind_folio: str | None = None
    bind_status: str | None = None
    bind_synced_at: datetime | None = None

    is_archived: bool
    created_at: datetime
    updated_at: datetime

    items: list[QuoteItemRead] = []
