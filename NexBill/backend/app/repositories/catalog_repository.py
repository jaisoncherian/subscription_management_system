"""Queries for the catalog: products, variants, taxes, plans and discounts."""
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


def get_product_by_name(name: str) -> Product | None:
    return db.session.scalar(db.select(Product).where(Product.name == name))


def get(model, item_id: int):
    return db.session.get(model, item_id)


def add(item):
    """Raises IntegrityError if the item's unique name or code is already taken."""
    db.session.add(item)
    db.session.flush()
    return item


def list_page(model, page: int, page_size: int) -> tuple[list, int]:
    """One page of a catalog model, oldest first, and the total count."""
    result = db.paginate(
        db.select(model).order_by(model.id), page=page, per_page=page_size, error_out=False
    )
    return result.items, result.total
