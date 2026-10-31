"""Schemas shared by several endpoints."""
from marshmallow import EXCLUDE, Schema, fields, validate


class PageQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
