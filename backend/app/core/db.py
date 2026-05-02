"""
Configuración de SQLAlchemy 2.x.

Provee:
- `engine` y `SessionLocal` para uso global
- `Base` declarativa que heredan los modelos
- `get_db` — dependencia FastAPI que cede una sesión por request y la cierra
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True,
    echo=False,  # cambia a True para debug SQL
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: una sesión por request, garantiza cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
