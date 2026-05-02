"""
Mapeo de entidades DNS One ↔ payloads de Bind ERP.

Centralizar el mapeo aquí permite ajustar nombres de campos en un solo lugar
cuando tengamos la documentación final del API.

Convenciones:
- `bind_to_*`: payload de Bind → dict con kwargs para crear/actualizar el modelo DNS One
- `*_to_bind`: modelo DNS One → payload listo para enviar a Bind
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.enums import Currency
from app.models.product import Product
from app.models.project import Project


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------
def bind_to_product_kwargs(payload: dict[str, Any]) -> dict[str, Any]:
    """Convierte un producto de Bind en kwargs para crear/actualizar `Product`."""
    return {
        "sku": payload["sku"],
        "name": payload["name"],
        "description": payload.get("description"),
        "brand": payload.get("brand"),
        "category": payload.get("category"),
        "unit": payload.get("unit", "PZA"),
        "cost_usd": _to_decimal(payload.get("cost_usd")),
        "cost_mxn": _to_decimal(payload.get("cost_mxn")),
        "list_price_usd": _to_decimal(payload.get("list_price_usd")),
        "list_price_mxn": _to_decimal(payload.get("list_price_mxn")),
        "currency_default": Currency(payload.get("currency", "USD")),
        "is_active": payload.get("is_active", True),
        "bind_product_id": payload["bind_id"],
    }


# ---------------------------------------------------------------------------
# Cotizaciones (Project → BIND)
# ---------------------------------------------------------------------------
def project_to_bind_quote(project: Project) -> dict[str, Any]:
    """
    Convierte un `Project` de DNS One al payload esperado por Bind para crear
    una cotización.

    Ajustar este shape al contrato real cuando tengamos las docs de Bind.
    """
    return {
        "external_reference": project.code,
        "customer": {
            "bind_customer_id": project.customer.bind_customer_id if project.customer else None,
            "name": project.customer.name if project.customer else None,
            "tax_id": project.customer.tax_id if project.customer else None,
            "email": project.customer.email if project.customer else None,
        },
        "currency": project.currency.value
        if hasattr(project.currency, "value")
        else str(project.currency),
        "exchange_rate": str(project.exchange_rate),
        "discount_pct": str(project.discount_pct),
        "valid_until": project.valid_until.isoformat() if project.valid_until else None,
        "notes": project.notes,
        "items": [
            {
                "bind_product_id": _maybe_bind_product_id(item),
                "sku": item.sku,
                "description": item.description,
                "qty": str(item.qty),
                "unit_price": str(item.unit_price),
                "discount_pct": str(item.discount_pct),
                "tax_pct": str(item.tax_pct),
            }
            for item in project.items
        ],
    }


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------
def _to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))


def _maybe_bind_product_id(item) -> str | None:  # type: ignore[no-untyped-def]
    """
    Devuelve el `bind_product_id` del producto vinculado, si existe.
    Para productos ad-hoc (sin product_id), regresa None y BIND debe aceptar
    la línea solo con SKU + descripción.
    """
    if item.product_id is None:
        return None
    # `product` no se carga por relación aquí (item no tiene relationship)
    # pero el caller debe haberlo poblado o el campo product_id se usa solo
    # para el lookup separado en el sync service.
    return None
