"""Modelo de usuario."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.role import Role


class User(Base, TimestampMixin):
    """Usuario de la aplicación."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)

    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role: Mapped["Role | None"] = relationship(back_populates="users", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    @property
    def permission_codes(self) -> set[str]:
        """
        Permisos efectivos del usuario.

        Superusers tienen todos los permisos implícitamente (se evalúa con `*`
        en los chequeos).
        """
        if self.is_superuser:
            return {"*"}
        if self.role is None:
            return set()
        return self.role.permission_codes
