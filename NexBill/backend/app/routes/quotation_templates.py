"""Quotation templates. Admins manage them, staff and admins can read them."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user

from app.core.decorators import roles_required
from app.models.enums import UserRole
from app.schemas.quotation import (
    TemplateInputSchema,
    TemplateListQuerySchema,
    TemplateSchema,
)
from app.services import quotation_service

quotation_templates_bp = Blueprint(
    "quotation_templates", __name__, url_prefix="/api/quotation-templates"
)


@quotation_templates_bp.post("")
@roles_required(UserRole.ADMIN)
def create_template():
    data = TemplateInputSchema().load(request.get_json())
    template = quotation_service.create_template(get_current_user(), **data)
    return jsonify(TemplateSchema().dump(template)), 201


@quotation_templates_bp.get("")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def list_templates():
    query = TemplateListQuerySchema().load(request.args.to_dict())
    items, total = quotation_service.list_templates(**query)
    return jsonify(
        {
            "items": TemplateSchema(many=True).dump(items),
            "total": total,
            "page": query["page"],
            "page_size": query["page_size"],
        }
    )


@quotation_templates_bp.get("/<int:template_id>")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def get_template(template_id):
    return jsonify(TemplateSchema().dump(quotation_service.get_template(template_id)))


@quotation_templates_bp.put("/<int:template_id>")
@roles_required(UserRole.ADMIN)
def update_template(template_id):
    data = TemplateInputSchema().load(request.get_json())
    template = quotation_service.update_template(get_current_user(), template_id, **data)
    return jsonify(TemplateSchema().dump(template))


@quotation_templates_bp.delete("/<int:template_id>")
@roles_required(UserRole.ADMIN)
def deactivate_template(template_id):
    template = quotation_service.deactivate_template(get_current_user(), template_id)
    return jsonify(TemplateSchema().dump(template))
