"""Schemas de usuario y rol."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class PermissionRead(ORMModel):
    id: int
    code: str
    description: str | None = None


class RoleRead(ORMModel):
    id: int
    name: str
    description: str | None = None
    is_system: bool
    permissions: list[PermissionRead] = []


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: str | None = None
    permission_codes: list[str] = []


class UserRead(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    role: RoleRead | None = None
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=200)
    role_id: int | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=200)
    role_id: int | None = None
    is_active: bool | None = None
