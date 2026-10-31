"""Customer list, used by staff to pick a customer for a subscription."""
from flask import Blueprint, jsonify, request

from app.core.decorators import roles_required
from app.models.enums import UserRole
from app.schemas.customer import CustomerListResponseSchema
from app.services import customer_service

customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")


@customers_bp.get("")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def list_customers():
    result = customer_service.list_customers(request.args.to_dict())
    return jsonify(CustomerListResponseSchema().dump(result))
