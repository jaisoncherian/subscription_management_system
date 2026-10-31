"""Queries for invoices and payments, including customer scoping.

Overdue is computed here, in the queries, and is never stored.

Reads take only_customer_id: None means every customer, so only pass None after
the service has established that the caller is staff or an admin. Customers
never see drafts, because a draft has not been issued to them yet.
"""
from datetime import date

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Invoice, Payment, invoice_number_seq
from app.models.enums import InvoiceStatus
from app.repositories import sequences


def next_number() -> str:
    return f"INV-{sequences.next_value(invoice_number_seq):06d}"


def add(invoice: Invoice) -> Invoice:
    """Raises IntegrityError if this subscription already has this period."""
    db.session.add(invoice)
    db.session.flush()
    return invoice


def add_payment(payment: Payment) -> Payment:
    db.session.add(payment)
    db.session.flush()
    return payment


def get_for_update(invoice_id: int) -> Invoice | None:
    """Lock the row, so that simultaneous payments cannot overpay it together."""
    return db.session.scalar(
        db.select(Invoice)
        .where(Invoice.id == invoice_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def get_visible(
    invoice_id: int, only_customer_id: int | None, today: date
) -> tuple[Invoice, bool] | None:
    """The invoice and whether it is overdue, or None if the caller may not see it."""
    query = _with_overdue(today).where(Invoice.id == invoice_id)
    row = db.session.execute(_scoped(query, only_customer_id)).first()
    return (row[0], row[1]) if row else None


def list_visible(
    only_customer_id: int | None,
    customer_id: int | None,
    status: str | None,
    overdue_only: bool,
    today: date,
    page: int,
    per_page: int,
) -> tuple[list[tuple[Invoice, bool]], int]:
    query = _scoped(_with_overdue(today), only_customer_id)
    if customer_id is not None:
        query = query.where(Invoice.customer_id == customer_id)
    if status is not None:
        query = query.where(Invoice.status == status)
    if overdue_only:
        query = query.where(_overdue_condition(today))

    total = db.session.scalar(
        db.select(db.func.count()).select_from(query.order_by(None).subquery())
    )
    rows = db.session.execute(
        query.order_by(Invoice.id.desc())
        .options(selectinload(Invoice.lines))
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).all()
    return [(row[0], row[1]) for row in rows], total


def list_payments(invoice_id: int) -> list[Payment]:
    return list(
        db.session.scalars(
            db.select(Payment)
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.payment_date, Payment.id)
        )
    )


def _overdue_condition(today: date):
    return db.and_(Invoice.status == InvoiceStatus.CONFIRMED, Invoice.due_date < today)


def _with_overdue(today: date):
    return db.select(Invoice, _overdue_condition(today).label("is_overdue"))


def _scoped(query, only_customer_id: int | None):
    if only_customer_id is None:
        return query
    return query.where(
        Invoice.customer_id == only_customer_id,
        Invoice.status != InvoiceStatus.DRAFT,
    )
