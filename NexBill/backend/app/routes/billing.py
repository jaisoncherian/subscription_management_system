"""Starting a billing run by hand. The same run is available as flask run-billing."""
from flask import Blueprint, jsonify
from flask_jwt_extended import get_current_user

from app.core.decorators import roles_required
from app.models.enums import UserRole
from app.services import billing_service

billing_bp = Blueprint("billing", __name__, url_prefix="/api/billing")


@billing_bp.post("/run")
@roles_required(UserRole.ADMIN)
def run_billing():
    return jsonify(billing_service.run_billing(get_current_user().id))
