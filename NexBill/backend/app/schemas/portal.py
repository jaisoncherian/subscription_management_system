"""Marshmallow validation for portal query params."""
from __future__ import annotations

from marshmallow import Schema, fields


class PaginationSchema(Schema):
    page = fields.Integer(load_default=1, validate=lambda value: value > 0)
    page_size = fields.Integer(load_default=25, validate=lambda value: 1 <= value <= 200)
