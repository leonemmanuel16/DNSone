"""Schemas de bitácoras de integración."""
from __future__ import annotations

from datetime import datetime

from app.models.enums import (
    BindSyncRunType,
    BindSyncStatus,
    IntegrationEventStatus,
    IntegrationProvider,
)
from app.schemas.common import ORMModel


class BindSyncLogRead(ORMModel):
    id: int
    run_type: BindSyncRunType
    status: BindSyncStatus
    started_at: datetime
    ended_at: datetime | None = None
    records_in: int
    records_out: int
    errors_count: int
    message: str | None = None
    created_at: datetime


class IntegrationEventRead(ORMModel):
    id: int
    provider: IntegrationProvider
    event_type: str
    status: IntegrationEventStatus
    payload_json: dict | None = None
    result_json: dict | None = None
    error_message: str | None = None
    project_id: int | None = None
    completed_at: datetime | None = None
    created_at: datetime
