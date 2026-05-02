"""
Tests unitarios de la lógica de pricing.

Cubre:
- Cálculo de partida individual (sin descuento, con descuento)
- Cálculo de proyecto (sin/con descuento global)
- Edge cases: cantidad cero, precio cero, partidas vacías
- Precisión decimal y redondeo
- Reglas comerciales: USD/MXN, IVA por línea, margen
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.pricing import (
    LineInput,
    calculate_line,
    calculate_project,
)


# ---------------------------------------------------------------------------
# calculate_line
# ---------------------------------------------------------------------------
class TestCalculateLine:
    def test_simple_line_no_discount(self):
        """100 USD * 2 unidades, sin descuento."""
        line = LineInput(
            qty=Decimal("2"),
            unit_cost=Decimal("60"),
            unit_price=Decimal("100"),
        )
        result = calculate_line(line)

        assert result.line_cost_total == Decimal("120.00")
        assert result.line_sale_gross == Decimal("200.00")
        assert result.line_sale_total == Decimal("200.00")
        # margen = (200 - 120) / 200 * 100 = 40%
        assert result.line_margin_pct == Decimal("40.0000")

    def test_line_with_10_percent_discount(self):
        """100 USD * 1 unidad con 10% de descuento."""
        line = LineInput(
            qty=Decimal("1"),
            unit_cost=Decimal("60"),
            unit_price=Decimal("100"),
            discount_pct=Decimal("10"),
        )
        result = calculate_line(line)

        assert result.line_sale_total == Decimal("90.00")
        # margen = (90 - 60) / 90 * 100 ≈ 33.3333%
        assert result.line_margin_pct == Decimal("33.3333")

    def test_line_zero_price_zero_margin(self):
        """Precio cero: margen 0 (por safe_div)."""
        line = LineInput(
            qty=Decimal("1"),
            unit_cost=Decimal("0"),
            unit_price=Decimal("0"),
        )
        result = calculate_line(line)
        assert result.line_sale_total == Decimal("0.00")
        assert result.line_margin_pct == Decimal("0.0000")

    def test_line_decimal_precision(self):
        """Verifica redondeo con valores que generarían .005."""
        line = LineInput(
            qty=Decimal("3"),
            unit_cost=Decimal("33.333"),
            unit_price=Decimal("66.667"),
        )
        result = calculate_line(line)
        # 3 * 33.333 = 99.999 → 100.00
        assert result.line_cost_total == Decimal("100.00")
        # 3 * 66.667 = 200.001 → 200.00
        assert result.line_sale_total == Decimal("200.00")


# ---------------------------------------------------------------------------
# calculate_project
# ---------------------------------------------------------------------------
class TestCalculateProject:
    def test_empty_project(self):
        """Cotización sin partidas: todos los totales en cero."""
        result = calculate_project([])

        assert result.subtotal_cost == Decimal("0.00")
        assert result.subtotal_sale == Decimal("0.00")
        assert result.discount_amount == Decimal("0.00")
        assert result.tax_total == Decimal("0.00")
        assert result.grand_total == Decimal("0.00")
        assert result.margin_pct == Decimal("0.0000")
        assert result.lines == []

    def test_single_line_no_global_discount(self):
        """1 partida, IVA 16%, sin descuento global."""
        lines = [
            LineInput(
                qty=Decimal("1"),
                unit_cost=Decimal("100"),
                unit_price=Decimal("200"),
                tax_pct=Decimal("16"),
            )
        ]
        result = calculate_project(lines)

        assert result.subtotal_cost == Decimal("100.00")
        assert result.subtotal_sale == Decimal("200.00")
        assert result.discount_amount == Decimal("0.00")
        assert result.tax_total == Decimal("32.00")  # 200 * 0.16
        assert result.grand_total == Decimal("232.00")
        assert result.margin_pct == Decimal("50.0000")

    def test_two_lines_with_global_discount(self):
        """
        2 partidas, IVA 16%, descuento global 10%.
        Verifica que el descuento global se aplica antes del IVA.

        Línea 1: 1 * 100 = 100
        Línea 2: 1 * 200 = 200
        Subtotal venta: 300
        Descuento global 10%: -30
        Base imponible: 270
        IVA 16% sobre 270: 43.20
        Total: 313.20
        """
        lines = [
            LineInput(qty=Decimal("1"), unit_cost=Decimal("60"), unit_price=Decimal("100")),
            LineInput(qty=Decimal("1"), unit_cost=Decimal("120"), unit_price=Decimal("200")),
        ]
        result = calculate_project(lines, global_discount_pct=Decimal("10"))

        assert result.subtotal_cost == Decimal("180.00")
        assert result.subtotal_sale == Decimal("300.00")
        assert result.discount_amount == Decimal("30.00")
        assert result.taxable_base == Decimal("270.00")
        assert result.tax_total == Decimal("43.20")
        assert result.grand_total == Decimal("313.20")
        # margen = (270 - 180) / 270 * 100 ≈ 33.3333%
        assert result.margin_pct == Decimal("33.3333")

    def test_per_line_discount_and_global_discount(self):
        """
        Verifica que ambos descuentos se aplican correctamente.

        Línea: qty=2, precio=100, descuento línea=20% → 2*100*0.8 = 160
        Subtotal: 160
        Descuento global 10%: -16
        Base imponible: 144
        IVA 16%: 23.04
        Total: 167.04
        """
        lines = [
            LineInput(
                qty=Decimal("2"),
                unit_cost=Decimal("50"),
                unit_price=Decimal("100"),
                discount_pct=Decimal("20"),
            ),
        ]
        result = calculate_project(lines, global_discount_pct=Decimal("10"))

        assert result.subtotal_sale == Decimal("160.00")
        assert result.discount_amount == Decimal("16.00")
        assert result.tax_total == Decimal("23.04")
        assert result.grand_total == Decimal("167.04")

    def test_mixed_tax_rates(self):
        """
        Partidas con distintos IVA (algunos productos 0% en MX).

        Línea 1: 100 * 16% = 16
        Línea 2: 100 * 0%  = 0
        Tax total: 16
        """
        lines = [
            LineInput(qty=Decimal("1"), unit_cost=Decimal("0"), unit_price=Decimal("100"), tax_pct=Decimal("16")),
            LineInput(qty=Decimal("1"), unit_cost=Decimal("0"), unit_price=Decimal("100"), tax_pct=Decimal("0")),
        ]
        result = calculate_project(lines)

        assert result.subtotal_sale == Decimal("200.00")
        assert result.tax_total == Decimal("16.00")
        assert result.grand_total == Decimal("216.00")

    def test_global_discount_out_of_range_raises(self):
        with pytest.raises(ValueError, match="global_discount_pct"):
            calculate_project([], global_discount_pct=Decimal("150"))
        with pytest.raises(ValueError, match="global_discount_pct"):
            calculate_project([], global_discount_pct=Decimal("-5"))

    def test_negative_margin(self):
        """Vendiendo bajo costo: margen negativo."""
        lines = [
            LineInput(qty=Decimal("1"), unit_cost=Decimal("150"), unit_price=Decimal("100")),
        ]
        result = calculate_project(lines)
        # margen = (100 - 150) / 100 * 100 = -50%
        assert result.margin_pct == Decimal("-50.0000")
