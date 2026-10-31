"""Request and response schemas for taxes, products, plans and discounts.

Everything the database CHECK constraints refuse is refused here first, so a
violation returns 422 and an IntegrityError can only mean a duplicate name.
"""
from decimal import Decimal

from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.models.enums import BillingPeriod, DiscountScope, DiscountType, ProductType

_MAX_MONEY = Decimal("9999999999.99")
_MAX_INT = 2_147_483_647


def _two_places(amount: Decimal) -> None:
    if amount.as_tuple().exponent < -2:
        raise ValidationError("Must have at most two decimal places.")


def _money(**kwargs) -> fields.Decimal:
    return fields.Decimal(
        validate=[validate.Range(min=0, max=_MAX_MONEY), _two_places], **kwargs
    )


def _percentage(**kwargs) -> fields.Decimal:
    return fields.Decimal(validate=[validate.Range(min=0, max=100), _two_places], **kwargs)


def _name(max_length: int) -> fields.String:
    return fields.String(
        required=True,
        validate=[validate.Length(max=max_length), validate.Regexp(r"\S", error="Must not be blank.")],
    )


def _positive_int(**kwargs) -> fields.Integer:
    return fields.Integer(strict=True, validate=validate.Range(min=1, max=_MAX_INT), **kwargs)


def _check_date_order(data: dict) -> None:
    valid_from, valid_to = data.get("valid_from"), data.get("valid_to")
    if valid_from and valid_to and valid_to < valid_from:
        raise ValidationError({"valid_to": ["Must not be before valid_from."]})


class TaxInputSchema(Schema):
    name = _name(100)
    rate = _percentage(required=True)


class TaxSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    rate = fields.Decimal(as_string=True, places=2)
    is_active = fields.Boolean()


class VariantInputSchema(Schema):
    attribute = _name(100)
    value = _name(100)
    extra_price = _money(load_default=Decimal("0.00"))


class ProductInputSchema(Schema):
    name = _name(150)
    description = fields.String(allow_none=True, validate=validate.Length(max=2000))
    product_type = fields.String(
        load_default=ProductType.SERVICE,
        validate=validate.OneOf([t.value for t in ProductType]),
    )
    sales_price = _money(required=True)
    cost_price = _money(load_default=Decimal("0.00"))
    variants = fields.List(fields.Nested(VariantInputSchema), load_default=list)

    @validates_schema
    def variants_are_unique(self, data, **kwargs):
        pairs = [(v["attribute"], v["value"]) for v in data.get("variants", [])]
        if len(pairs) != len(set(pairs)):
            raise ValidationError({"variants": ["Each attribute and value can appear only once."]})


class VariantSchema(Schema):
    id = fields.Integer()
    attribute = fields.String()
    value = fields.String()
    extra_price = fields.Decimal(as_string=True, places=2)
    is_active = fields.Boolean()


class ProductSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String()
    product_type = fields.String()
    sales_price = fields.Decimal(as_string=True, places=2)
    cost_price = fields.Decimal(as_string=True, places=2)
    is_active = fields.Boolean()
    variants = fields.List(fields.Nested(VariantSchema))


class PlanInputSchema(Schema):
    name = _name(150)
    price = _money(load_default=Decimal("0.00"))
    billing_period = fields.String(
        required=True, validate=validate.OneOf([p.value for p in BillingPeriod])
    )
    billing_interval = _positive_int(load_default=1)
    min_quantity = _positive_int(load_default=1)
    valid_from = fields.Date(allow_none=True)
    valid_to = fields.Date(allow_none=True)
    is_auto_close = fields.Boolean(load_default=False)
    is_closable = fields.Boolean(load_default=True)
    is_pausable = fields.Boolean(load_default=False)
    is_renewable = fields.Boolean(load_default=False)

    @validates_schema
    def dates_are_in_order(self, data, **kwargs):
        _check_date_order(data)


class PlanSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    price = fields.Decimal(as_string=True, places=2)
    billing_period = fields.String()
    billing_interval = fields.Integer()
    min_quantity = fields.Integer()
    valid_from = fields.Date()
    valid_to = fields.Date()
    is_auto_close = fields.Boolean()
    is_closable = fields.Boolean()
    is_pausable = fields.Boolean()
    is_renewable = fields.Boolean()
    is_active = fields.Boolean()


class DiscountInputSchema(Schema):
    code = _name(50)
    name = _name(150)
    discount_type = fields.String(
        required=True, validate=validate.OneOf([t.value for t in DiscountType])
    )
    scope = fields.String(
        load_default=DiscountScope.SUBSCRIPTION,
        validate=validate.OneOf([s.value for s in DiscountScope]),
    )
    value = fields.Decimal(
        required=True,
        validate=[validate.Range(min=0, min_inclusive=False, max=_MAX_MONEY), _two_places],
    )
    min_purchase = _money(load_default=Decimal("0.00"))
    min_quantity = _positive_int(load_default=1)
    valid_from = fields.Date(allow_none=True)
    valid_to = fields.Date(allow_none=True)
    usage_limit = fields.Integer(
        strict=True, allow_none=True, validate=validate.Range(min=0, max=_MAX_INT)
    )
    product_ids = fields.List(fields.Integer(strict=True), load_default=list)

    @validates_schema
    def rules_hold_together(self, data, **kwargs):
        _check_date_order(data)
        if data.get("discount_type") == DiscountType.PERCENT and data.get("value", 0) > 100:
            raise ValidationError({"value": ["A percent discount cannot exceed 100."]})
        if data.get("scope") == DiscountScope.PRODUCT and not data.get("product_ids"):
            raise ValidationError({"product_ids": ["A product discount needs at least one product."]})
        if data.get("scope") == DiscountScope.SUBSCRIPTION and data.get("product_ids"):
            raise ValidationError({"product_ids": ["Only a product discount can list products."]})


class DiscountSchema(Schema):
    id = fields.Integer()
    code = fields.String()
    name = fields.String()
    discount_type = fields.String()
    scope = fields.String()
    value = fields.Decimal(as_string=True, places=2)
    min_purchase = fields.Decimal(as_string=True, places=2)
    min_quantity = fields.Integer()
    valid_from = fields.Date()
    valid_to = fields.Date()
    usage_limit = fields.Integer()
    usage_count = fields.Integer()
    is_active = fields.Boolean()
    product_ids = fields.Function(lambda discount: [product.id for product in discount.products])
