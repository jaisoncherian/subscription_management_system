"""Invoices: reading, the state machine, and sending."""
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core import clock
from app.core.errors import Conflict, NotFound
from app.models import Invoice, User
from app.models.enums import InvoiceStatus as Status
from app.repositories import audit_repository, invoice_repository, transaction
from app.services import mail_service
from app.services.access import customer_scope


def _confirm(invoice: Invoice, now: datetime) -> Status:
    invoice.confirmed_at = now
    # Nothing can ever be paid against a zero total, so it is already settled.
    if invoice.total == 0:
        invoice.paid_at = now
        return Status.PAID
    return Status.CONFIRMED


def _cancel(invoice: Invoice, now: datetime) -> Status:
    if invoice.amount_paid > 0:
        raise Conflict(
            "This invoice has payments recorded, so it cannot be cancelled.",
            code="invoice_has_payments",
        )
    invoice.cancelled_at = now
    return Status.CANCELLED


@dataclass(frozen=True)
class InvoiceTransition:
    sources: frozenset[Status]
    # Returns the new status. Raises to refuse the move.
    apply: callable


# The whole state machine, apart from Paid, which only a payment can reach.
TRANSITIONS = {
    "confirm": InvoiceTransition(frozenset({Status.DRAFT}), _confirm),
    "cancel": InvoiceTransition(frozenset({Status.DRAFT, Status.CONFIRMED}), _cancel),
}


def get_invoice(viewer: User, invoice_id: int) -> Invoice:
    """Another customer's invoice looks exactly like one that does not exist."""
    row = invoice_repository.get_visible(invoice_id, customer_scope(viewer), clock.today())
    if row is None:
        raise NotFound("Invoice not found.")
    invoice, invoice.is_overdue = row
    return invoice


def list_invoices(
    viewer: User,
    customer_id: int | None,
    status: str | None,
    overdue: bool,
    page: int,
    per_page: int,
) -> tuple[list[Invoice], int]:
    rows, total = invoice_repository.list_visible(
        customer_scope(viewer), customer_id, status, overdue, clock.today(), page, per_page
    )
    invoices = []
    for invoice, invoice.is_overdue in rows:
        invoices.append(invoice)
    return invoices, total


def apply_action(actor: User, invoice_id: int, action: str) -> Invoice:
    transition = TRANSITIONS[action]
    invoice = invoice_repository.get_for_update(invoice_id)
    if invoice is None:
        raise NotFound("Invoice not found.")

    previous_status = invoice.status
    if previous_status not in transition.sources:
        raise Conflict(
            f"Cannot {action} an invoice that is {previous_status}.",
            code="invalid_transition",
        )
    invoice.status = transition.apply(invoice, datetime.now(timezone.utc))
    audit_repository.record(
        f"invoice.{action}",
        "invoice",
        invoice.id,
        actor.id,
        {"from": previous_status, "to": invoice.status},
    )
    transaction.commit()
    return get_invoice(actor, invoice_id)


def send_invoice(actor: User, invoice_id: int) -> Invoice:
    invoice = invoice_repository.get_for_update(invoice_id)
    if invoice is None:
        raise NotFound("Invoice not found.")
    if invoice.status not in (Status.CONFIRMED, Status.PAID):
        raise Conflict(
            f"Cannot send an invoice that is {invoice.status}. Confirm it first.",
            code="invoice_not_sendable",
        )

    invoice.sent_at = datetime.now(timezone.utc)
    audit_repository.record("invoice.sent", "invoice", invoice.id, actor.id)
    transaction.commit()

    mail_service.send_email(
        invoice.customer_snapshot["email"],
        f"Invoice {invoice.invoice_number} from Brightloop Software",
        _email_body(invoice),
    )
    return get_invoice(actor, invoice_id)


def _email_body(invoice: Invoice) -> str:
    lines = "\n".join(
        f"- {line.description} x {line.quantity}: {line.line_total:.2f}"
        for line in invoice.lines
    )
    return (
        f"Hello {invoice.customer_snapshot['name']},\n\n"
        f"Invoice {invoice.invoice_number} for {invoice.period_start} to "
        f"{invoice.period_end} is ready.\n\n"
        f"{lines}\n\n"
        f"Total: {invoice.total:.2f}\n"
        f"Balance due: {invoice.total - invoice.amount_paid:.2f}\n"
        f"Due date: {invoice.due_date}\n\n"
        "Thank you,\nBrightloop Software"
    )
