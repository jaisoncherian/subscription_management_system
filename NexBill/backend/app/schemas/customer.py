"""Request and response schemas for the customer list."""
from marshmallow import EXCLUDE, Schema, fields, validate


class CustomerListQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))


class CustomerListItemSchema(Schema):
    """Deliberately only these three fields: this list is for picking a customer."""

    id = fields.Integer()
    name = fields.String()
    email = fields.String()


class CustomerListResponseSchema(Schema):
    items = fields.List(fields.Nested(CustomerListItemSchema))
    page = fields.Integer()
    page_size = fields.Integer()
    total = fields.Integer()
