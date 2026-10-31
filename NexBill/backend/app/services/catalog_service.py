"""Catalog: creating and listing taxes, products, plans and discounts."""
from sqlalchemy.exc import IntegrityError

from app.core.errors import Conflict, NotFound, ValidationFailed
from app.models import Discount, Plan, Product, ProductVariant, Tax, User
from app.repositories import audit_repository, catalog_repository, transaction


def create_tax(actor: User, **data) -> Tax:
    return _create(actor, Tax(**data), "tax")


def create_product(actor: User, variants: list[dict], **data) -> Product:
    product = Product(**data, variants=[ProductVariant(**variant) for variant in variants])
    return _create(actor, product, "product")


def create_plan(actor: User, **data) -> Plan:
    return _create(actor, Plan(**data), "plan")


def create_discount(actor: User, product_ids: list[int], **data) -> Discount:
    products = [catalog_repository.get_product(product_id) for product_id in product_ids]
    if None in products:
        raise ValidationFailed(fields={"product_ids": ["Unknown product."]})
    return _create(actor, Discount(**data, products=products), "discount", unique_field="code")


def list_items(model: type, page: int, page_size: int) -> tuple[list, int]:
    return catalog_repository.list_page(model, page, page_size)


def deactivate(actor: User, model: type, item_id: int, entity: str):
    """Catalog items are never deleted, because subscriptions refer back to them."""
    item = catalog_repository.get(model, item_id)
    if item is None:
        raise NotFound(f"This {entity} was not found.")
    item.is_active = False
    audit_repository.record(f"{entity}.deactivated", entity, item.id, actor.id)
    transaction.commit()
    return item


def _create(actor: User, item, entity: str, unique_field: str = "name"):
    try:
        catalog_repository.add(item)
        audit_repository.record(f"{entity}.created", entity, item.id, actor.id)
        transaction.commit()
    except IntegrityError:
        transaction.rollback()
        message = f"A {entity} with this {unique_field} already exists."
        raise Conflict(message, code="name_taken", fields={unique_field: [message]}) from None
    return item
