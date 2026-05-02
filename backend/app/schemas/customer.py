"""Schemas de cliente."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class CustomerBase(BaseModel):
    code: str | None = Field(default=None, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    tax_id: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    contact_name: str | None = Field(default=None, max_length=255)
    billing_address: str | None = Field(default=None, max_length=500)
    shipping_address: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    tax_id: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    contact_name: str | None = None
    billing_address: str | None = None
    shipping_address: str | None = None
    is_active: bool | None = None


class CustomerRead(ORMModel, CustomerBase):
    id: int
    bind_customer_id: str | None = None
    bind_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
