"""Configuración centralizada de logging."""
from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """
    Configura el logger root con formato consistente para todo el backend.

    Idempotente: limpia handlers existentes para evitar duplicados al recargar
    en desarrollo.
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Limpiar handlers previos (uvicorn --reload puede dispararlos múltiples veces)
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)

    # Bajar verbosidad de librerías ruidosas
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
