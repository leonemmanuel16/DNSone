"""
Helpers para aritmética decimal consistente.

Reglas del proyecto:
- Precios y costos: 2 decimales en totales, 4 en costos/precios unitarios
- Porcentajes: 4 decimales (para precisión interna)
- Redondeo: ROUND_HALF_UP (estándar comercial: 0.5 redondea hacia arriba)
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

# Quantizadores reutilizables
Q_MONEY = Decimal("0.01")        # 2 decimales para totales
Q_UNIT = Decimal("0.0001")        # 4 decimales para costos/precios unitarios
Q_PCT = Decimal("0.0001")         # 4 decimales para porcentajes


def to_money(value: Decimal | float | int | str) -> Decimal:
    """Cuantiza a 2 decimales para mostrar como dinero (totales, subtotales)."""
    return Decimal(str(value)).quantize(Q_MONEY, rounding=ROUND_HALF_UP)


def to_unit(value: Decimal | float | int | str) -> Decimal:
    """Cuantiza a 4 decimales para precios/costos unitarios."""
    return Decimal(str(value)).quantize(Q_UNIT, rounding=ROUND_HALF_UP)


def to_pct(value: Decimal | float | int | str) -> Decimal:
    """Cuantiza a 4 decimales para porcentajes (descuentos, impuestos, márgenes)."""
    return Decimal(str(value)).quantize(Q_PCT, rounding=ROUND_HALF_UP)


def safe_div(numerator: Decimal, denominator: Decimal) -> Decimal:
    """División segura: regresa 0 si el denominador es 0."""
    if denominator == 0:
        return Decimal("0")
    return numerator / denominator
