"""Modelos de bitácora de integraciones externas (BIND, Syscom)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin
from app.models.enums import (
    BindSyncRunType,
    BindSyncStatus,
    IntegrationEventStatus,
    IntegrationProvider,
)


class BindSyncLog(Base, TimestampMixin):
    """Bitácora de cada corrida de sync con BIND."""

    __tablename__ = "bind_sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    run_type: Mapped[BindSyncRunType] = mapped_column(String(30), nullable=False, index=True)
    status: Mapped[BindSyncStatus] = mapped_column(
        String(20), default=BindSyncStatus.RUNNING, nullable=False, index=True
    )

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    records_in: Mapped[int] = mapped_column(Integer, default=0)
    records_out: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)

    message: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<BindSyncLog {self.run_type} {self.status}>"

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()


class IntegrationEvent(Base, TimestampMixin):
    """
    Evento de integración con un proveedor externo.

    Útil para diagnóstico (qué payload se envió, qué respondió BIND, etc.) y
    para reintento idempotente en fase 2.
    """

    __tablename__ = "integration_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    provider: Mapped[IntegrationProvider] = mapped_column(String(20), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    status: Mapped[IntegrationEventStatus] = mapped_column(
        String(20), default=IntegrationEventStatus.PENDING, nullable=False, index=True
    )

    payload_json: Mapped[dict | None] = mapped_column(JSON)
    result_json: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)

    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<IntegrationEvent {self.provider}.{self.event_type} {self.status}>"
