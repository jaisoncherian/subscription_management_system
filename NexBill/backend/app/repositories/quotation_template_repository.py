"""Queries for quotation templates."""
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import QuotationTemplate, TemplateLine


def get_by_id(template_id: int) -> QuotationTemplate | None:
    return db.session.get(QuotationTemplate, template_id)


def list_page(
    page: int, per_page: int, include_inactive: bool
) -> tuple[list[QuotationTemplate], int]:
    query = db.select(QuotationTemplate).order_by(QuotationTemplate.name)
    if not include_inactive:
        query = query.where(QuotationTemplate.is_active.is_(True))
    query = query.options(
        selectinload(QuotationTemplate.plan),
        selectinload(QuotationTemplate.lines).selectinload(TemplateLine.product),
    )
    result = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return result.items, result.total


def add(template: QuotationTemplate) -> QuotationTemplate:
    """Raises IntegrityError if the name is already taken."""
    db.session.add(template)
    db.session.flush()
    return template
