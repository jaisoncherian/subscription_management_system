"""Marshmallow validation for report query params."""
from __future__ import annotations

from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class ReportDateRangeSchema(Schema):
    date_from = fields.Date(load_default=None)
    date_to = fields.Date(load_default=None)
    group = fields.String(load_default="month")
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Integer(load_default=25, validate=validate.Range(min=1, max=100))

    @validates_schema
    def validate_date_order(self, data, **kwargs):
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        if date_from and date_to and date_to < date_from:
            raise ValidationError(
                {"date_to": ["date_to must be greater than or equal to date_from."]},
                field_name="date_to",
            )


class RevenueGroupSchema(ReportDateRangeSchema):
    group = fields.String(required=True, validate=validate.OneOf(["month"]))
