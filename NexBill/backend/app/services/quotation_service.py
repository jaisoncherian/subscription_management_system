"""Quotation templates: reusable plan, lines and validity for new subscriptions."""
from sqlalchemy.exc import IntegrityError

from app.core.errors import Conflict, NotFound, ValidationFailed
from app.models import Plan, QuotationTemplate, TemplateLine, User
from app.repositories import (
    audit_repository,
    catalog_repository,
    quotation_template_repository,
    transaction,
)


def create_template(
    actor: User, name: str, plan_id: int, validity_days: int, lines: list[dict]
) -> QuotationTemplate:
    plan = _require_active_plan(plan_id)
    template = QuotationTemplate(
        name=name,
        plan_id=plan.id,
        validity_days=validity_days,
        lines=_build_lines(plan, lines),
    )
    try:
        quotation_template_repository.add(template)
        audit_repository.record("quotation_template.created", "quotation_template", template.id, actor.id)
        transaction.commit()
    except IntegrityError:
        transaction.rollback()
        raise _name_taken() from None
    return template


def update_template(
    actor: User,
    template_id: int,
    name: str,
    plan_id: int,
    validity_days: int,
    lines: list[dict],
) -> QuotationTemplate:
    """Replace the template. Subscriptions already created from it do not change."""
    template = get_template(template_id)
    plan = _require_active_plan(plan_id)
    new_lines = _build_lines(plan, lines)
    try:
        # Replacing the lines loads the old ones, which flushes the new name,
        # so a duplicate name can surface here and not only at commit.
        template.name = name
        template.plan_id = plan.id
        template.validity_days = validity_days
        template.lines = new_lines
        audit_repository.record("quotation_template.updated", "quotation_template", template.id, actor.id)
        transaction.commit()
    except IntegrityError:
        transaction.rollback()
        raise _name_taken() from None
    return template


def deactivate_template(actor: User, template_id: int) -> QuotationTemplate:
    """Templates are never deleted, because subscriptions refer back to them."""
    template = get_template(template_id)
    template.is_active = False
    audit_repository.record("quotation_template.deactivated", "quotation_template", template.id, actor.id)
    transaction.commit()
    return template


def get_template(template_id: int) -> QuotationTemplate:
    template = quotation_template_repository.get_by_id(template_id)
    if template is None:
        raise NotFound("Quotation template not found.")
    return template


def list_templates(
    page: int, page_size: int, include_inactive: bool
) -> tuple[list[QuotationTemplate], int]:
    return quotation_template_repository.list_page(page, page_size, include_inactive)


def _require_active_plan(plan_id: int) -> Plan:
    plan = catalog_repository.get_plan(plan_id)
    if plan is None or not plan.is_active:
        raise ValidationFailed(fields={"plan_id": ["Unknown or inactive plan."]})
    return plan


def _build_lines(plan: Plan, lines: list[dict]) -> list[TemplateLine]:
    errors = {}
    for index, line in enumerate(lines):
        line_errors = _line_errors(plan, line)
        if line_errors:
            errors[index] = line_errors
    if errors:
        raise ValidationFailed(fields={"lines": errors})

    return [
        TemplateLine(
            product_id=line["product_id"],
            variant_id=line.get("variant_id"),
            tax_id=line.get("tax_id"),
            quantity=line["quantity"],
        )
        for line in lines
    ]


def _line_errors(plan: Plan, line: dict) -> dict[str, list[str]]:
    errors = {}

    product = catalog_repository.get_product(line["product_id"])
    if product is None or not product.is_active:
        errors["product_id"] = ["Unknown or inactive product."]

    variant_id = line.get("variant_id")
    if variant_id is not None:
        variant = catalog_repository.get_variant(variant_id)
        if variant is None or not variant.is_active:
            errors["variant_id"] = ["Unknown or inactive variant."]
        elif variant.product_id != line["product_id"]:
            errors["variant_id"] = ["This variant belongs to a different product."]

    tax_id = line.get("tax_id")
    if tax_id is not None:
        tax = catalog_repository.get_tax(tax_id)
        if tax is None or not tax.is_active:
            errors["tax_id"] = ["Unknown or inactive tax."]

    if line["quantity"] < plan.min_quantity:
        errors["quantity"] = [f"This plan needs a quantity of at least {plan.min_quantity}."]

    return errors


def _name_taken() -> Conflict:
    message = "A quotation template with this name already exists."
    return Conflict(message, code="name_taken", fields={"name": [message]})
