"""Schemas compartidos."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base para schemas que se construyen desde modelos ORM."""

    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    """Respuesta paginada genérica."""

    items: list[T]
    total: int
    page: int = 1
    page_size: int = 50


class MessageResponse(BaseModel):
    """Respuesta simple con mensaje."""

    message: str
