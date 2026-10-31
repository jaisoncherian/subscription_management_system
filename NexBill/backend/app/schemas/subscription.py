"""Request and response schemas for subscriptions."""
from marshmallow import Schema, fields, validate

from app.models.enums import SubscriptionStatus
from app.schemas.common import PageQuerySchema


class SubscriptionCreateSchema(Schema):
    customer_id = fields.Integer(required=True, strict=True)
    template_id = fields.Integer(required=True, strict=True)
    start_date = fields.Date(allow_none=True)
    expires_on = fields.Date(allow_none=True)
    discount_id = fields.Integer(strict=True, allow_none=True)
    notes = fields.String(allow_none=True, validate=validate.Length(max=2000))


class SubscriptionListQuerySchema(PageQuerySchema):
    status = fields.String(validate=validate.OneOf([s.value for s in SubscriptionStatus]))


class SubscriptionLineSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    product_name = fields.String(attribute="product.name")
    variant_id = fields.Integer()
    tax_id = fields.Integer()
    quantity = fields.Integer()
    unit_price = fields.Decimal(as_string=True, places=2)


class SubscriptionSchema(Schema):
    id = fields.Integer()
    subscription_number = fields.String()
    status = fields.String()
    customer_id = fields.Integer()
    customer_name = fields.String(attribute="customer.name")
    plan_id = fields.Integer()
    plan_name = fields.String(attribute="plan.name")
    template_id = fields.Integer()
    discount_id = fields.Integer()
    quotation_valid_until = fields.Date()
    start_date = fields.Date()
    next_billing_date = fields.Date()
    expires_on = fields.Date()
    closed_at = fields.DateTime()
    notes = fields.String()
    lines = fields.List(fields.Nested(SubscriptionLineSchema))
