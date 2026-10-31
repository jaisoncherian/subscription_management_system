"""Reporting endpoints for staff/admin users."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.core.decorators import roles_required
from app.schemas.report import ReportDateRangeSchema, RevenueGroupSchema
from app.services.report_service import (
    get_overdue_invoices,
    get_revenue_by_period,
    get_summary,
)

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.get("/summary")
@roles_required("admin", "staff")
def summary():
    params = ReportDateRangeSchema().load(request.args.to_dict())
    payload = get_summary(date_from=params.get("date_from"), date_to=params.get("date_to"))
    return jsonify(payload)


@reports_bp.get("/revenue")
@roles_required("admin", "staff")
def revenue():
    params = RevenueGroupSchema().load(request.args.to_dict())
    payload = get_revenue_by_period(
        date_from=params.get("date_from"),
        date_to=params.get("date_to"),
        group=params.get("group", "month"),
    )
    return jsonify(payload)


@reports_bp.get("/overdue")
@roles_required("admin", "staff")
def overdue():
    params = ReportDateRangeSchema().load(request.args.to_dict())
    payload = get_overdue_invoices(
        date_from=params.get("date_from"),
        date_to=params.get("date_to"),
        page=params.get("page", 1),
        page_size=params.get("page_size", 25),
    )
    return jsonify(payload)
