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
    variant_label = fields.Function(
        lambda line: f"{line.variant.attribute}: {line.variant.value}" if line.variant else None
    )
    tax_id = fields.Integer()
    tax_name = fields.String(attribute="tax.name")
    quantity = fields.Integer()
    unit_price = fields.Decimal(as_string=True, places=2)
    amount = fields.Function(lambda line: f"{line.quantity * line.unit_price:.2f}")


class SubscriptionSchema(Schema):
    id = fields.Integer()
    subscription_number = fields.String()
    status = fields.String()
    # Only set on a single subscription, not in lists. See subscription_service.
    allowed_actions = fields.List(fields.String())
    customer_id = fields.Integer()
    customer_name = fields.String(attribute="customer.name")
    customer_email = fields.String(attribute="customer.email")
    plan_id = fields.Integer()
    plan_name = fields.String(attribute="plan.name")
    billing_period = fields.String(attribute="plan.billing_period")
    template_id = fields.Integer()
    discount_id = fields.Integer()
    quotation_valid_until = fields.Date()
    start_date = fields.Date()
    next_billing_date = fields.Date()
    expires_on = fields.Date()
    closed_at = fields.DateTime()
    notes = fields.String()
    lines = fields.List(fields.Nested(SubscriptionLineSchema))
