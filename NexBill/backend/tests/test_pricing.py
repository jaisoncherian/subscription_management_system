"""Pricing is pure calculation, so these tests need no database."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services import pricing_service

TODAY = date(2026, 6, 15)


def make_line(price="100.00", quantity=1, tax_rate=None, product_id=1):
    tax = SimpleNamespace(rate=Decimal(tax_rate)) if tax_rate else None
    return SimpleNamespace(
        product_id=product_id, unit_price=Decimal(price), quantity=quantity, tax=tax
    )


def make_discount(**overrides):
    values = {
        "id": 7,
        "is_active": True,
        "valid_from": None,
        "valid_to": None,
        "usage_limit": None,
        "usage_count": 0,
        "min_purchase": Decimal("0.00"),
        "min_quantity": 1,
        "scope": "subscription",
        "discount_type": "percent",
        "value": Decimal("10.00"),
        "products": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


# Variant extra price


def test_unit_price_adds_the_variant_extra():
    product = SimpleNamespace(sales_price=Decimal("1000.00"))
    variant = SimpleNamespace(extra_price=Decimal("560.00"))

    assert pricing_service.unit_price(product, variant) == Decimal("1560.00")
    assert pricing_service.unit_price(product, None) == Decimal("1000.00")


# Tax per line


def test_each_line_is_taxed_at_its_own_rate():
    priced = pricing_service.price_lines(
        [make_line("100.00", 2, "18.00"), make_line("50.00", 1, "5.00"), make_line("10.00")]
    )

    assert [line.tax_amount for line in priced.lines] == [
        Decimal("36.00"),
        Decimal("2.50"),
        Decimal("0.00"),
    ]
    assert priced.subtotal == Decimal("260.00")
    assert priced.tax_total == Decimal("38.50")
    assert priced.total == Decimal("298.50")


def test_tax_rounds_half_up_to_the_cent():
    priced = pricing_service.price_lines([make_line("0.50", 1, "1.00")])

    assert priced.lines[0].tax_amount == Decimal("0.01")


def test_tax_is_charged_on_the_discounted_amount():
    priced = pricing_service.price_lines(
        [make_line("100.00", 1, "10.00")], make_discount(value=Decimal("50.00"))
    )

    assert priced.discount_total == Decimal("50.00")
    assert priced.tax_total == Decimal("5.00")
    assert priced.total == Decimal("55.00")


# Eligibility


@pytest.mark.parametrize(
    "overrides",
    [
        {"is_active": False},
        {"valid_from": date(2026, 6, 16)},
        {"valid_to": date(2026, 6, 14)},
        {"usage_limit": 3, "usage_count": 3},
        {"min_purchase": Decimal("100.01")},
        {"min_quantity": 2},
    ],
)
def test_discount_is_not_eligible(overrides):
    assert not pricing_service.is_discount_eligible(
        make_discount(**overrides), [make_line()], TODAY
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"valid_from": TODAY, "valid_to": TODAY},
        {"usage_limit": 3, "usage_count": 2},
        {"usage_limit": None, "usage_count": 5000},
        {"min_purchase": Decimal("100.00")},
        {"min_quantity": 1},
    ],
)
def test_discount_is_eligible_on_its_boundaries(overrides):
    assert pricing_service.is_discount_eligible(
        make_discount(**overrides), [make_line()], TODAY
    )


def test_product_discount_needs_a_matching_line():
    discount = make_discount(scope="product", products=[SimpleNamespace(id=9)])

    assert not pricing_service.is_discount_eligible(discount, [make_line(product_id=1)], TODAY)
    assert pricing_service.is_discount_eligible(discount, [make_line(product_id=9)], TODAY)


def test_product_discount_minimums_count_only_matching_lines():
    discount = make_discount(
        scope="product", products=[SimpleNamespace(id=9)], min_purchase=Decimal("500.00")
    )
    lines = [make_line("400.00", product_id=9), make_line("400.00", product_id=1)]

    assert not pricing_service.is_discount_eligible(discount, lines, TODAY)


# Applying a discount


def test_percent_discount_applies_to_every_line_for_subscription_scope():
    priced = pricing_service.price_lines(
        [make_line("100.00"), make_line("50.00")], make_discount()
    )

    assert [line.discount_amount for line in priced.lines] == [Decimal("10.00"), Decimal("5.00")]
    assert all(line.discount_id == 7 for line in priced.lines)


def test_product_discount_leaves_other_lines_alone():
    discount = make_discount(scope="product", products=[SimpleNamespace(id=9)])

    priced = pricing_service.price_lines(
        [make_line("100.00", product_id=9), make_line("100.00", product_id=1)], discount
    )

    assert [line.discount_amount for line in priced.lines] == [Decimal("10.00"), Decimal("0.00")]
    assert [line.discount_id for line in priced.lines] == [7, None]


def test_fixed_discount_is_shared_and_adds_up_exactly():
    discount = make_discount(discount_type="fixed", value=Decimal("10.00"))

    priced = pricing_service.price_lines(
        [make_line("33.33"), make_line("33.33"), make_line("33.34")], discount
    )

    assert sum(line.discount_amount for line in priced.lines) == Decimal("10.00")
    assert priced.discount_total == Decimal("10.00")


def test_fixed_discount_cannot_exceed_the_order_value():
    discount = make_discount(discount_type="fixed", value=Decimal("500.00"))

    priced = pricing_service.price_lines([make_line("100.00", 1, "18.00")], discount)

    assert priced.discount_total == Decimal("100.00")
    assert priced.tax_total == Decimal("0.00")
    assert priced.total == Decimal("0.00")


def test_totals_always_add_up():
    discount = make_discount(value=Decimal("12.50"))

    priced = pricing_service.price_lines(
        [make_line("19.99", 3, "18.00"), make_line("7.77", 2, "5.00")], discount
    )

    assert priced.total == priced.subtotal - priced.discount_total + priced.tax_total
    assert priced.total == sum(line.total for line in priced.lines)
