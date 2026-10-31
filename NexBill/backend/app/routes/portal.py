"""Customer portal endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.core.decorators import roles_required
from app.schemas.portal import PaginationSchema
from app.services.portal_service import (
    list_customer_invoices,
    list_customer_subscriptions,
)

portal_bp = Blueprint("portal", __name__, url_prefix="/api/portal")


@portal_bp.get("/subscriptions")
@roles_required("customer")
def subscriptions():
    params = PaginationSchema().load(request.args.to_dict())
    user_id = get_jwt_identity()
    payload = list_customer_subscriptions(
        user_id,
        page=params.get("page", 1),
        page_size=params.get("page_size", 25),
    )
    return jsonify(payload)


@portal_bp.get("/invoices")
@roles_required("customer")
def invoices():
    params = PaginationSchema().load(request.args.to_dict())
    user_id = get_jwt_identity()
    payload = list_customer_invoices(
        user_id,
        page=params.get("page", 1),
        page_size=params.get("page_size", 25),
    )
    return jsonify(payload)
