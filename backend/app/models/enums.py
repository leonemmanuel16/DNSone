"""Enums de dominio compartidos por modelos y schemas."""
from __future__ import annotations

from enum import StrEnum


class Currency(StrEnum):
    """Monedas soportadas."""

    USD = "USD"
    MXN = "MXN"


class ProjectStatus(StrEnum):
    """Estados del ciclo de vida de un proyecto-cotización."""

    DRAFT = "draft"            # creado, aún no enviado
    SENT = "sent"              # enviado a cliente / BIND
    APPROVED = "approved"      # aprobado por cliente
    REJECTED = "rejected"      # rechazado por cliente
    CONVERTED = "converted"    # convertido a venta / orden
    CANCELLED = "cancelled"    # cancelado internamente


class BindSyncRunType(StrEnum):
    """Tipo de ejecución del sync con BIND."""

    PRODUCTS = "products"
    CUSTOMERS = "customers"
    QUOTES_STATUS = "quotes_status"
    MANUAL = "manual"


class BindSyncStatus(StrEnum):
    """Resultado de una corrida de sync."""

    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"


class IntegrationProvider(StrEnum):
    """Proveedores externos integrados."""

    BIND = "bind"
    SYSCOM = "syscom"


class IntegrationEventStatus(StrEnum):
    """Estado de un evento de integración."""

    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
