"""Staff account management."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user

from app.core.decorators import roles_required
from app.models.enums import UserRole
from app.schemas.auth import CreateStaffSchema, UserSchema
from app.schemas.common import PageQuerySchema
from app.services import user_service

staff_bp = Blueprint("staff", __name__, url_prefix="/api/staff")


@staff_bp.post("")
@roles_required(UserRole.ADMIN)
def create_staff():
    data = CreateStaffSchema().load(request.get_json())
    user = user_service.create_staff(get_current_user().id, **data)
    return jsonify(UserSchema().dump(user)), 201


@staff_bp.get("")
@roles_required(UserRole.ADMIN)
def list_staff():
    query = PageQuerySchema().load(request.args.to_dict())
    items, total = user_service.list_staff(query["page"], query["page_size"])
    return jsonify(
        {
            "items": UserSchema(many=True).dump(items),
            "total": total,
            "page": query["page"],
            "page_size": query["page_size"],
        }
    )
