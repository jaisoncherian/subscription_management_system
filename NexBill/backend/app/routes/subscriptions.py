"""Subscriptions. Staff and admins manage them, customers can read their own."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user, jwt_required

from app.core.decorators import roles_required
from app.models.enums import UserRole
from app.schemas.subscription import (
    SubscriptionCreateSchema,
    SubscriptionListQuerySchema,
    SubscriptionSchema,
)
from app.services import subscription_service

subscriptions_bp = Blueprint("subscriptions", __name__, url_prefix="/api/subscriptions")

# Quoted because the converter cannot parse a bare hyphen, as in send-quotation.
ACTIONS = ",".join(f"'{action}'" for action in subscription_service.TRANSITIONS)


@subscriptions_bp.post("")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def create_subscription():
    data = SubscriptionCreateSchema().load(request.get_json())
    subscription = subscription_service.create_from_template(get_current_user(), **data)
    return jsonify(SubscriptionSchema().dump(subscription)), 201


@subscriptions_bp.get("")
@jwt_required()
def list_subscriptions():
    query = SubscriptionListQuerySchema().load(request.args.to_dict())
    items, total = subscription_service.list_subscriptions(
        get_current_user(), query.get("status"), query["page"], query["per_page"]
    )
    return jsonify(
        {
            "items": SubscriptionSchema(many=True).dump(items),
            "total": total,
            "page": query["page"],
            "per_page": query["per_page"],
        }
    )


@subscriptions_bp.get("/<int:subscription_id>")
@jwt_required()
def get_subscription(subscription_id):
    subscription = subscription_service.get_subscription(get_current_user(), subscription_id)
    return jsonify(SubscriptionSchema().dump(subscription))


@subscriptions_bp.post(f"/<int:subscription_id>/<any({ACTIONS}):action>")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def apply_action(subscription_id, action):
    subscription = subscription_service.apply_action(
        get_current_user(), subscription_id, action
    )
    return jsonify(SubscriptionSchema().dump(subscription))
