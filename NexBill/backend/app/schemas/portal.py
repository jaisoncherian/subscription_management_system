"""Marshmallow validation for portal query params."""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class PaginationSchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Integer(load_default=25, validate=validate.Range(min=1, max=100))
