"""
Scheduler basado en APScheduler.

Programa los jobs de sincronización con BIND cada `SYNC_INTERVAL_MINUTES`.
La implementación de los jobs reales vive en `app.integrations.bind.bind_sync_service`.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone as pytz_timezone

from app.core.config import settings

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _job_sync_products() -> None:
    """Job: sync de productos desde BIND. Importación lazy para evitar ciclos."""
    from app.integrations.bind.bind_sync_service import sync_products_from_bind

    try:
        sync_products_from_bind()
    except Exception:
        logger.exception("Falló sync_products_from_bind")


def _job_sync_quote_status() -> None:
    """Job: sync de estatus de cotizaciones enviadas a BIND."""
    from app.integrations.bind.bind_sync_service import sync_quote_status_from_bind

    try:
        sync_quote_status_from_bind()
    except Exception:
        logger.exception("Falló sync_quote_status_from_bind")


def start_scheduler() -> None:
    """Inicia el scheduler con los jobs de sync."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler ya está corriendo, ignorando start_scheduler()")
        return

    tz = pytz_timezone(settings.APP_TIMEZONE)
    _scheduler = BackgroundScheduler(timezone=tz)

    interval = IntervalTrigger(minutes=settings.SYNC_INTERVAL_MINUTES, timezone=tz)

    _scheduler.add_job(
        _job_sync_products,
        trigger=interval,
        id="bind_sync_products",
        name="Sincroniza productos desde BIND",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    _scheduler.add_job(
        _job_sync_quote_status,
        trigger=interval,
        id="bind_sync_quote_status",
        name="Sincroniza estatus de cotizaciones desde BIND",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    _scheduler.start()
    logger.info(
        "Scheduler iniciado con %d jobs (intervalo=%d min, tz=%s)",
        len(_scheduler.get_jobs()),
        settings.SYNC_INTERVAL_MINUTES,
        settings.APP_TIMEZONE,
    )


def shutdown_scheduler() -> None:
    """Detiene el scheduler limpiamente."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler detenido")
    _scheduler = None
