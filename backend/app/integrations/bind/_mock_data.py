"""
Datos mock para Bind ERP, usados cuando `BIND_USE_MOCK=true`.

La forma exacta del payload se ajustará cuando tengamos documentación oficial
del API de Bind. Se mantiene en un archivo separado para reemplazo rápido.
"""
from __future__ import annotations

from typing import Any

# Productos típicos del catálogo DNS (networking + seguridad)
MOCK_BIND_PRODUCTS: list[dict[str, Any]] = [
    {
        "bind_id": "BND-P-0001",
        "sku": "UBQ-USW-LITE-8POE",
        "name": "Ubiquiti UniFi Switch Lite 8 PoE",
        "description": "Switch administrable 8 puertos Gigabit con 4 PoE+",
        "brand": "Ubiquiti",
        "category": "Switches",
        "unit": "PZA",
        "cost_usd": "120.00",
        "list_price_usd": "189.00",
        "currency": "USD",
        "is_active": True,
    },
    {
        "bind_id": "BND-P-0002",
        "sku": "UBQ-U6-LR",
        "name": "Ubiquiti UniFi 6 Long-Range AP",
        "description": "Access Point WiFi 6 de largo alcance",
        "brand": "Ubiquiti",
        "category": "Access Points",
        "unit": "PZA",
        "cost_usd": "210.00",
        "list_price_usd": "299.00",
        "currency": "USD",
        "is_active": True,
    },
    {
        "bind_id": "BND-P-0003",
        "sku": "MTK-CCR2004",
        "name": "Mikrotik CCR2004-1G-12S+2XS",
        "description": "Cloud Core Router 12 SFP+ 2 x 25G",
        "brand": "Mikrotik",
        "category": "Routers",
        "unit": "PZA",
        "cost_usd": "1450.00",
        "list_price_usd": "1990.00",
        "currency": "USD",
        "is_active": True,
    },
    {
        "bind_id": "BND-P-0004",
        "sku": "FT-FG-60F",
        "name": "Fortinet FortiGate 60F",
        "description": "Firewall NGFW 10 Gbps SD-WAN",
        "brand": "Fortinet",
        "category": "Firewalls",
        "unit": "PZA",
        "cost_usd": "650.00",
        "list_price_usd": "950.00",
        "currency": "USD",
        "is_active": True,
    },
    {
        "bind_id": "BND-P-0005",
        "sku": "HK-DS-2CD2143",
        "name": "Hikvision DS-2CD2143G2-IS",
        "description": "Cámara IP domo 4MP IR 30m",
        "brand": "Hikvision",
        "category": "Videovigilancia",
        "unit": "PZA",
        "cost_usd": "85.00",
        "list_price_usd": "140.00",
        "currency": "USD",
        "is_active": True,
    },
]


def mock_create_quote_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Devuelve una respuesta simulada de Bind al crear una cotización."""
    import uuid

    return {
        "bind_quote_id": f"BND-Q-{uuid.uuid4().hex[:10].upper()}",
        "folio": f"COT-{uuid.uuid4().hex[:6].upper()}",
        "status": "borrador",
        "echo_payload": payload,
    }


def mock_quote_status(bind_quote_id: str) -> dict[str, Any]:
    """Devuelve un estatus simulado para una cotización."""
    return {
        "bind_quote_id": bind_quote_id,
        "status": "enviada",
        "updated_at": "2026-05-01T10:00:00Z",
    }
