"""Invoices and payments. Staff and admins manage them, customers can read their own."""
import secrets

from flask import Blueprint, jsonify, make_response, render_template, request
from flask_jwt_extended import get_current_user, jwt_required

from app.core.decorators import roles_required
from app.core.http import content_security_policy
from app.models.enums import UserRole
from app.schemas.invoice import (
    InvoiceListQuerySchema,
    InvoiceSchema,
    PaymentCreateSchema,
    PaymentSchema,
)
from app.services import invoice_service, payment_service

invoices_bp = Blueprint("invoices", __name__, url_prefix="/api/invoices")

ACTIONS = ",".join(f"'{action}'" for action in invoice_service.TRANSITIONS)


@invoices_bp.get("")
@jwt_required()
def list_invoices():
    query = InvoiceListQuerySchema().load(request.args.to_dict())
    items, total = invoice_service.list_invoices(
        get_current_user(),
        query.get("customer_id"),
        query.get("status"),
        query["overdue"],
        query["page"],
        query["page_size"],
    )
    return jsonify(
        {
            "items": InvoiceSchema(many=True).dump(items),
            "total": total,
            "page": query["page"],
            "page_size": query["page_size"],
        }
    )


@invoices_bp.get("/<int:invoice_id>")
@jwt_required()
def get_invoice(invoice_id):
    invoice = invoice_service.get_invoice(get_current_user(), invoice_id)
    return jsonify(InvoiceSchema().dump(invoice))


@invoices_bp.get("/<int:invoice_id>/print")
@jwt_required()
def print_invoice(invoice_id):
    invoice = invoice_service.get_invoice(get_current_user(), invoice_id)
    # The page's one script, its print button, is allowed by a nonce for this response.
    nonce = secrets.token_urlsafe(16)
    response = make_response(render_template("invoice.html", invoice=invoice, nonce=nonce))
    response.headers["Content-Security-Policy"] = content_security_policy(f"'nonce-{nonce}'")
    return response


@invoices_bp.post(f"/<int:invoice_id>/<any({ACTIONS}):action>")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def apply_action(invoice_id, action):
    invoice = invoice_service.apply_action(get_current_user(), invoice_id, action)
    return jsonify(InvoiceSchema().dump(invoice))


@invoices_bp.post("/<int:invoice_id>/send")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def send_invoice(invoice_id):
    invoice = invoice_service.send_invoice(get_current_user(), invoice_id)
    return jsonify(InvoiceSchema().dump(invoice))


@invoices_bp.get("/<int:invoice_id>/payments")
@jwt_required()
def list_payments(invoice_id):
    payments = payment_service.list_payments(get_current_user(), invoice_id)
    return jsonify(PaymentSchema(many=True).dump(payments))


@invoices_bp.post("/<int:invoice_id>/payments")
@roles_required(UserRole.ADMIN, UserRole.STAFF)
def record_payment(invoice_id):
    data = PaymentCreateSchema().load(request.get_json())
    payment = payment_service.record_payment(get_current_user(), invoice_id, **data)
    return jsonify(PaymentSchema().dump(payment)), 201
