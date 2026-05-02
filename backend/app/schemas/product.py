"""Schemas de producto."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import Currency
from app.schemas.common import ORMModel


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)
    unit: str = Field(default="PZA", max_length=20)
    cost_usd: Decimal | None = None
    cost_mxn: Decimal | None = None
    list_price_usd: Decimal | None = None
    list_price_mxn: Decimal | None = None
    currency_default: Currency = Currency.USD
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = None
    name: str | None = None
    description: str | None = None
    brand: str | None = None
    category: str | None = None
    unit: str | None = None
    cost_usd: Decimal | None = None
    cost_mxn: Decimal | None = None
    list_price_usd: Decimal | None = None
    list_price_mxn: Decimal | None = None
    currency_default: Currency | None = None
    is_active: bool | None = None


class ProductRead(ORMModel, ProductBase):
    id: int
    bind_product_id: str | None = None
    bind_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
