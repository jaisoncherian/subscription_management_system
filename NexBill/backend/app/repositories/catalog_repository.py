"""Read-only catalog lookups. Catalog create and edit live with the catalog feature."""
from app.extensions import db
from app.models import Discount, Plan, Product, ProductVariant, Tax


def get_plan(plan_id: int) -> Plan | None:
    return db.session.get(Plan, plan_id)


def get_product(product_id: int) -> Product | None:
    return db.session.get(Product, product_id)


def get_variant(variant_id: int) -> ProductVariant | None:
    return db.session.get(ProductVariant, variant_id)


def get_tax(tax_id: int) -> Tax | None:
    return db.session.get(Tax, tax_id)


def get_discount(discount_id: int) -> Discount | None:
    return db.session.get(Discount, discount_id)
