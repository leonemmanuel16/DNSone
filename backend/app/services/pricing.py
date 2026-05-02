"""
Lógica de cálculo comercial — totales, descuentos, impuestos y margen.

Todo se calcula con `Decimal` para evitar errores de redondeo. Los resultados
se cuantizan al final con `to_money()` (2 decimales) o `to_pct()` (4 decimales).

Convención del descuento global:
- El descuento global de la cotización se aplica **proporcionalmente** sobre
  cada partida ANTES de calcular el impuesto de esa partida. Esto da el
  comportamiento esperado: el IVA se cobra solo sobre lo que el cliente
  realmente paga.

Convención del margen:
- El margen se calcula sobre la base imponible (subtotal - descuento global),
  no sobre el subtotal bruto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable

from app.utils.decimal_helpers import safe_div, to_money, to_pct


# ---------------------------------------------------------------------------
# Estructuras de entrada / salida
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LineInput:
    """Entrada para calcular una partida."""

    qty: Decimal
    unit_cost: Decimal
    unit_price: Decimal
    discount_pct: Decimal = Decimal("0")  # descuento de línea
    tax_pct: Decimal = Decimal("16")      # IVA por línea (default 16%)


@dataclass(frozen=True)
class LineCalc:
    """Resultado del cálculo de una partida."""

    line_cost_total: Decimal      # qty * unit_cost
    line_sale_gross: Decimal      # qty * unit_price (antes de descuento de línea)
    line_sale_total: Decimal      # qty * unit_price * (1 - discount_pct/100)
    line_margin_pct: Decimal      # margen de la partida en %


@dataclass(frozen=True)
class ProjectCalc:
    """Resultado del cálculo agregado del proyecto-cotización."""

    subtotal_cost: Decimal        # suma de line_cost_total
    subtotal_sale: Decimal        # suma de line_sale_total (post descuento de línea, pre global)
    discount_amount: Decimal      # monto del descuento global
    taxable_base: Decimal         # subtotal_sale - discount_amount
    tax_total: Decimal            # suma de impuestos por línea sobre base imponible
    grand_total: Decimal          # taxable_base + tax_total
    margin_pct: Decimal           # margen sobre taxable_base
    lines: list[LineCalc] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Funciones puras
# ---------------------------------------------------------------------------
def calculate_line(line: LineInput) -> LineCalc:
    """
    Calcula los totales de una partida.

    - line_cost_total = qty * unit_cost
    - line_sale_gross = qty * unit_price
    - line_sale_total = line_sale_gross * (1 - discount_pct/100)
    - line_margin_pct = (line_sale_total - line_cost_total) / line_sale_total * 100
    """
    qty = Decimal(line.qty)
    unit_cost = Decimal(line.unit_cost)
    unit_price = Decimal(line.unit_price)
    disc_pct = Decimal(line.discount_pct)

    line_cost_total = qty * unit_cost
    line_sale_gross = qty * unit_price
    discount_factor = (Decimal("100") - disc_pct) / Decimal("100")
    line_sale_total = line_sale_gross * discount_factor

    margin = safe_div(line_sale_total - line_cost_total, line_sale_total) * Decimal("100")

    return LineCalc(
        line_cost_total=to_money(line_cost_total),
        line_sale_gross=to_money(line_sale_gross),
        line_sale_total=to_money(line_sale_total),
        line_margin_pct=to_pct(margin),
    )


def calculate_project(
    lines: Iterable[LineInput],
    *,
    global_discount_pct: Decimal | float | int | str = Decimal("0"),
) -> ProjectCalc:
    """
    Calcula totales del proyecto-cotización.

    Aplica el descuento global proporcionalmente sobre cada partida antes de
    calcular el impuesto de esa partida.

    Args:
        lines: iterable de partidas de entrada.
        global_discount_pct: descuento global en porcentaje (0-100).

    Returns:
        ProjectCalc con todos los totales cuantizados a 2 decimales.
    """
    global_disc = Decimal(str(global_discount_pct))
    if global_disc < 0 or global_disc > 100:
        raise ValueError(f"global_discount_pct fuera de rango: {global_disc}")

    line_calcs: list[LineCalc] = []
    subtotal_cost = Decimal("0")
    subtotal_sale = Decimal("0")
    tax_total = Decimal("0")

    discount_factor = (Decimal("100") - global_disc) / Decimal("100")

    for line in lines:
        lc = calculate_line(line)
        line_calcs.append(lc)

        subtotal_cost += lc.line_cost_total
        subtotal_sale += lc.line_sale_total

        # Aplicar descuento global proporcional y luego impuesto de la línea
        line_after_global = lc.line_sale_total * discount_factor
        line_tax = line_after_global * (Decimal(line.tax_pct) / Decimal("100"))
        tax_total += line_tax

    discount_amount = subtotal_sale * (global_disc / Decimal("100"))
    taxable_base = subtotal_sale - discount_amount
    grand_total = taxable_base + tax_total

    margin_pct = safe_div(taxable_base - subtotal_cost, taxable_base) * Decimal("100")

    return ProjectCalc(
        subtotal_cost=to_money(subtotal_cost),
        subtotal_sale=to_money(subtotal_sale),
        discount_amount=to_money(discount_amount),
        taxable_base=to_money(taxable_base),
        tax_total=to_money(tax_total),
        grand_total=to_money(grand_total),
        margin_pct=to_pct(margin_pct),
        lines=line_calcs,
    )


# ---------------------------------------------------------------------------
# Helper para integrar con modelos ORM
# ---------------------------------------------------------------------------
def quote_item_to_input(item) -> LineInput:  # type: ignore[no-untyped-def]
    """Convierte un `app.models.QuoteItem` a `LineInput` (sin importar el modelo aquí)."""
    return LineInput(
        qty=Decimal(item.qty),
        unit_cost=Decimal(item.unit_cost or 0),
        unit_price=Decimal(item.unit_price),
        discount_pct=Decimal(item.discount_pct or 0),
        tax_pct=Decimal(item.tax_pct or 0),
    )
