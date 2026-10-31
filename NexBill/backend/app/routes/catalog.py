"""Catalog. Admins create items, staff and admins can read them."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user

from app.core.decorators import roles_required
from app.models import Discount, Plan, Product, Tax
from app.models.enums import UserRole
from app.schemas.catalog import (
    DiscountInputSchema,
    DiscountSchema,
    PlanInputSchema,
    PlanSchema,
    ProductInputSchema,
    ProductSchema,
    TaxInputSchema,
    TaxSchema,
)
from app.schemas.common import PageQuerySchema
from app.services import catalog_service

catalog_bp = Blueprint("catalog", __name__, url_prefix="/api")


def _page(model, schema):
    query = PageQuerySchema().load(request.args.to_dict())
    items, total = catalog_service.list_items(model, query["page"], query["page_size"])
    return jsonify(
        {
            "items": schema(many=True).dump(items),
            "total": total,
            "page": query["page"],
            "page_size": query["page_size"],
        }
    )


@catalog_bp.post("/taxes")
@roles_required(UserRole.ADMIN)
def create_tax():
    data = TaxInputSchema().load(request.get_json())
    return jsonify(TaxSchema().dump(catalog_service.create_tax(get_current_user(), **data))), 201


@catalog_bp.get("/taxes")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def list_taxes():
    return _page(Tax, TaxSchema)


@catalog_bp.delete("/taxes/<int:item_id>")
@roles_required(UserRole.ADMIN)
def deactivate_tax(item_id):
    return jsonify(TaxSchema().dump(catalog_service.deactivate(get_current_user(), Tax, item_id, "tax")))


@catalog_bp.post("/products")
@roles_required(UserRole.ADMIN)
def create_product():
    data = ProductInputSchema().load(request.get_json())
    return jsonify(ProductSchema().dump(catalog_service.create_product(get_current_user(), **data))), 201


@catalog_bp.get("/products")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def list_products():
    return _page(Product, ProductSchema)


@catalog_bp.delete("/products/<int:item_id>")
@roles_required(UserRole.ADMIN)
def deactivate_product(item_id):
    return jsonify(ProductSchema().dump(catalog_service.deactivate(get_current_user(), Product, item_id, "product")))


@catalog_bp.post("/plans")
@roles_required(UserRole.ADMIN)
def create_plan():
    data = PlanInputSchema().load(request.get_json())
    return jsonify(PlanSchema().dump(catalog_service.create_plan(get_current_user(), **data))), 201


@catalog_bp.get("/plans")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def list_plans():
    return _page(Plan, PlanSchema)


@catalog_bp.delete("/plans/<int:item_id>")
@roles_required(UserRole.ADMIN)
def deactivate_plan(item_id):
    return jsonify(PlanSchema().dump(catalog_service.deactivate(get_current_user(), Plan, item_id, "plan")))


@catalog_bp.post("/discounts")
@roles_required(UserRole.ADMIN)
def create_discount():
    data = DiscountInputSchema().load(request.get_json())
    return jsonify(DiscountSchema().dump(catalog_service.create_discount(get_current_user(), **data))), 201


@catalog_bp.get("/discounts")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def list_discounts():
    return _page(Discount, DiscountSchema)


@catalog_bp.delete("/discounts/<int:item_id>")
@roles_required(UserRole.ADMIN)
def deactivate_discount(item_id):
    return jsonify(DiscountSchema().dump(catalog_service.deactivate(get_current_user(), Discount, item_id, "discount")))
