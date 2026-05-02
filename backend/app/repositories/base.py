"""
Repositorio genérico CRUD.

Patrón thin: mientras los endpoints sean simples mantenemos lógica directa con
la sesión de SQLAlchemy. Esta clase está disponible para casos donde valga la
pena encapsular queries (ej. búsquedas complejas, joins repetidos).
"""
from __future__ import annotations

from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD genérico mínimo."""

    def __init__(self, db: Session, model: Type[ModelT]) -> None:
        self.db = db
        self.model = model

    def get(self, pk: int) -> ModelT | None:
        return self.db.get(self.model, pk)

    def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        return self.db.execute(
            select(self.model).offset(offset).limit(limit)
        ).scalars().all()

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()
