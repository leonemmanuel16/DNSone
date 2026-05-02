"""
Stub de cliente Syscom — implementación pendiente.

Syscom es el proveedor mayorista de tecnología de DNS. Este módulo dejará el
punto de extensión claro: cuando llegue la fase de integración, completar
los métodos siguiendo el mismo patrón que `BindClient`.
"""
from __future__ import annotations

from typing import Any


class SyscomClient:
    """Placeholder. Implementar cuando se contrate API key de Syscom."""

    def __init__(self) -> None:
        raise NotImplementedError(
            "SyscomClient aún no está implementado. "
            "Ver `docs/decisions.md` para el plan de integración."
        )

    def get_product_availability(self, sku: str) -> dict[str, Any]:
        raise NotImplementedError

    def get_product_cost(self, sku: str) -> dict[str, Any]:
        raise NotImplementedError
