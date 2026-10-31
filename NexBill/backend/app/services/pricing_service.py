"""Prices. Module 5 adds tax and discount calculation here."""
from decimal import Decimal

from app.models import Product, ProductVariant


def unit_price(product: Product, variant: ProductVariant | None) -> Decimal:
    """Product base price plus the variant's extra price, e.g. 1000 + 560."""
    extra = variant.extra_price if variant else Decimal("0")
    return product.sales_price + extra
