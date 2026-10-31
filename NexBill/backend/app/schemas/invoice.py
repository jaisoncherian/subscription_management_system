"""Request and response schemas for invoices, payments and billing runs."""
from decimal import Decimal

from marshmallow import Schema, ValidationError, fields, validate

from app.models.enums import InvoiceStatus, PaymentMethod
from app.schemas.common import PageQuerySchema


def _validate_payment_amount(amount: Decimal) -> None:
    if amount <= 0:
        raise ValidationError("Must be greater than zero.")
    if amount.as_tuple().exponent < -2:
        raise ValidationError("Must have at most two decimal places.")


class InvoiceListQuerySchema(PageQuerySchema):
    status = fields.String(validate=validate.OneOf([s.value for s in InvoiceStatus]))
    customer_id = fields.Integer()
    overdue = fields.Boolean(load_default=False)


class InvoiceLineSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    description = fields.String()
    quantity = fields.Integer()
    unit_price = fields.Decimal(as_string=True, places=2)
    tax_name = fields.String()
    tax_rate = fields.Decimal(as_string=True, places=2)
    tax_amount = fields.Decimal(as_string=True, places=2)
    discount_amount = fields.Decimal(as_string=True, places=2)
    line_total = fields.Decimal(as_string=True, places=2)


class InvoiceSchema(Schema):
    id = fields.Integer()
    invoice_number = fields.String()
    status = fields.String()
    is_overdue = fields.Boolean()
    # Only set on a single invoice, not in lists. See invoice_service.
    allowed_actions = fields.List(fields.String())
    subscription_id = fields.Integer()
    customer_id = fields.Integer()
    customer_snapshot = fields.Dict()
    period_start = fields.Date()
    period_end = fields.Date()
    invoice_date = fields.Date()
    due_date = fields.Date()
    subtotal = fields.Decimal(as_string=True, places=2)
    discount_total = fields.Decimal(as_string=True, places=2)
    tax_total = fields.Decimal(as_string=True, places=2)
    total = fields.Decimal(as_string=True, places=2)
    amount_paid = fields.Decimal(as_string=True, places=2)
    balance_due = fields.Function(lambda invoice: f"{invoice.total - invoice.amount_paid:.2f}")
    confirmed_at = fields.DateTime()
    sent_at = fields.DateTime()
    paid_at = fields.DateTime()
    cancelled_at = fields.DateTime()
    lines = fields.List(fields.Nested(InvoiceLineSchema))


class PaymentCreateSchema(Schema):
    method = fields.String(
        required=True, validate=validate.OneOf([m.value for m in PaymentMethod])
    )
    amount = fields.Decimal(required=True, validate=_validate_payment_amount)
    payment_date = fields.Date(allow_none=True)
    note = fields.String(allow_none=True, validate=validate.Length(max=2000))


class PaymentSchema(Schema):
    id = fields.Integer()
    invoice_id = fields.Integer()
    invoice_number = fields.String(attribute="invoice.invoice_number")
    customer_name = fields.Function(lambda payment: payment.invoice.customer_snapshot.get("name"))
    method = fields.String()
    amount = fields.Decimal(as_string=True, places=2)
    payment_date = fields.Date()
    note = fields.String()
    created_at = fields.DateTime()
