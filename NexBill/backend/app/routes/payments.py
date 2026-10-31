"""Every payment, for staff and admins."""
from flask import Blueprint, jsonify, request

from app.core.decorators import roles_required
from app.models.enums import UserRole
from app.schemas.common import PageQuerySchema
from app.schemas.invoice import PaymentSchema
from app.services import payment_service

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")


@payments_bp.get("")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def list_payments():
    query = PageQuerySchema().load(request.args.to_dict())
    items, total = payment_service.list_all(query["page"], query["page_size"])
    return jsonify(
        {
            "items": PaymentSchema(many=True).dump(items),
            "total": total,
            "page": query["page"],
            "page_size": query["page_size"],
        }
    )
