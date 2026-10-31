"""Prices: variant extras, discount eligibility and allocation, and tax per line.

Everything here is pure calculation. Claiming a discount changes the database,
so that belongs to the billing run.
"""
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.models import Discount, Product, ProductVariant, SubscriptionLine
from app.models.enums import DiscountScope, DiscountType

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
HUNDRED = Decimal("100")


def round_money(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def unit_price(product: Product, variant: ProductVariant | None) -> Decimal:
    """Product base price plus the variant's extra price, e.g. 1000 + 560."""
    extra = variant.extra_price if variant else ZERO
    return product.sales_price + extra


@dataclass(frozen=True)
class PricedLine:
    source: SubscriptionLine
    subtotal: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    discount_id: int | None


@dataclass(frozen=True)
class PricedDocument:
    lines: list[PricedLine]
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal


def is_discount_eligible(
    discount: Discount, lines: list[SubscriptionLine], on_date: date
) -> bool:
    """Whether the discount can apply. The minimums count only the lines in its scope."""
    if not discount.is_active:
        return False
    if discount.valid_from and on_date < discount.valid_from:
        return False
    if discount.valid_to and on_date > discount.valid_to:
        return False
    if discount.usage_limit is not None and discount.usage_count >= discount.usage_limit:
        return False

    scoped = _lines_in_scope(discount, lines)
    if not scoped:
        return False
    purchase = sum((_subtotal(line) for line in scoped), ZERO)
    quantity = sum(line.quantity for line in scoped)
    return purchase >= discount.min_purchase and quantity >= discount.min_quantity


def price_lines(
    lines: list[SubscriptionLine], discount: Discount | None = None
) -> PricedDocument:
    """Price the lines. Tax is charged on the amount left after the discount.

    Pass a discount only once it has been found eligible and claimed.
    """
    discounts = _allocate_discount(discount, lines) if discount else {}

    priced = []
    for line in lines:
        subtotal = _subtotal(line)
        discount_amount = discounts.get(id(line), ZERO)
        tax_rate = line.tax.rate if line.tax else ZERO
        tax_amount = round_money((subtotal - discount_amount) * tax_rate / HUNDRED)
        priced.append(
            PricedLine(
                source=line,
                subtotal=subtotal,
                discount_amount=discount_amount,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total=subtotal - discount_amount + tax_amount,
                discount_id=discount.id if discount and id(line) in discounts else None,
            )
        )

    return PricedDocument(
        lines=priced,
        subtotal=sum((line.subtotal for line in priced), ZERO),
        discount_total=sum((line.discount_amount for line in priced), ZERO),
        tax_total=sum((line.tax_amount for line in priced), ZERO),
        total=sum((line.total for line in priced), ZERO),
    )


def _subtotal(line: SubscriptionLine) -> Decimal:
    return round_money(line.unit_price * line.quantity)


def _lines_in_scope(
    discount: Discount, lines: list[SubscriptionLine]
) -> list[SubscriptionLine]:
    if discount.scope == DiscountScope.SUBSCRIPTION:
        return list(lines)
    product_ids = {product.id for product in discount.products}
    return [line for line in lines if line.product_id in product_ids]


def _allocate_discount(
    discount: Discount, lines: list[SubscriptionLine]
) -> dict[int, Decimal]:
    """The discount amount for each line in scope, keyed by id(line)."""
    scoped = _lines_in_scope(discount, lines)
    if discount.discount_type == DiscountType.PERCENT:
        return {
            id(line): round_money(_subtotal(line) * discount.value / HUNDRED)
            for line in scoped
        }

    # A fixed amount is shared in proportion to each line's value, and can
    # never exceed the value of the lines. The last line takes the rounding
    # remainder, so that the parts always add up to the whole.
    base = sum((_subtotal(line) for line in scoped), ZERO)
    amount = min(discount.value, base)
    allocated = {}
    remaining = amount
    for index, line in enumerate(scoped):
        if index == len(scoped) - 1:
            share = remaining
        else:
            share = round_money(amount * _subtotal(line) / base) if base else ZERO
        allocated[id(line)] = share
        remaining -= share
    return allocated
