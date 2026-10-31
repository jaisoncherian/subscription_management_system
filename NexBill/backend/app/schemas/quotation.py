"""Request and response schemas for quotation templates."""
from marshmallow import Schema, fields, validate

from app.schemas.common import PageQuerySchema


class TemplateLineInputSchema(Schema):
    product_id = fields.Integer(required=True, strict=True)
    variant_id = fields.Integer(strict=True, allow_none=True)
    tax_id = fields.Integer(strict=True, allow_none=True)
    quantity = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))


class TemplateInputSchema(Schema):
    name = fields.String(
        required=True,
        validate=[validate.Length(max=150), validate.Regexp(r"\S", error="Must not be blank.")],
    )
    plan_id = fields.Integer(required=True, strict=True)
    validity_days = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    lines = fields.List(
        fields.Nested(TemplateLineInputSchema), required=True, validate=validate.Length(min=1)
    )


class TemplateListQuerySchema(PageQuerySchema):
    include_inactive = fields.Boolean(load_default=False)


class TemplateLineSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    product_name = fields.String(attribute="product.name")
    variant_id = fields.Integer()
    tax_id = fields.Integer()
    quantity = fields.Integer()


class TemplateSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    plan_id = fields.Integer()
    plan_name = fields.String(attribute="plan.name")
    validity_days = fields.Integer()
    is_active = fields.Boolean()
    lines = fields.List(fields.Nested(TemplateLineSchema))
