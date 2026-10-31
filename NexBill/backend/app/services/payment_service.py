"""Recording payments against invoices."""
from datetime import date, datetime, timezone
from decimal import Decimal

from app.core import clock
from app.core.errors import Conflict, NotFound, ValidationFailed
from app.models import Payment, User
from app.models.enums import InvoiceStatus
from app.repositories import audit_repository, invoice_repository, transaction
from app.services import invoice_service


def record_payment(
    actor: User,
    invoice_id: int,
    method: str,
    amount: Decimal,
    payment_date: date | None = None,
    note: str | None = None,
) -> Payment:
    payment_date = payment_date or clock.today()
    if payment_date > clock.today():
        raise ValidationFailed(fields={"payment_date": ["Must not be in the future."]})

    # Holding the row lock makes the balance check and the update one step, so
    # simultaneous payments cannot each see enough balance and overpay together.
    invoice = invoice_repository.get_for_update(invoice_id)
    if invoice is None:
        raise NotFound("Invoice not found.")
    if invoice.status != InvoiceStatus.CONFIRMED:
        raise Conflict(
            f"Cannot record a payment on an invoice that is {invoice.status}.",
            code="invoice_not_payable",
        )

    balance = invoice.total - invoice.amount_paid
    if amount > balance:
        message = f"This payment is more than the balance due of {balance:.2f}."
        raise Conflict(message, code="overpayment", fields={"amount": [message]})

    payment = invoice_repository.add_payment(
        Payment(
            invoice_id=invoice.id,
            recorded_by_user_id=actor.id,
            method=method,
            amount=amount,
            payment_date=payment_date,
            note=note,
        )
    )
    invoice.amount_paid += amount
    if invoice.amount_paid == invoice.total:
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.now(timezone.utc)

    audit_repository.record(
        "payment.recorded",
        "invoice",
        invoice.id,
        actor.id,
        {"payment_id": payment.id, "amount": str(amount), "method": method},
    )
    transaction.commit()
    return payment


def list_payments(viewer: User, invoice_id: int) -> list[Payment]:
    # Goes through the invoice first, so that customer scoping applies.
    invoice = invoice_service.get_invoice(viewer, invoice_id)
    return invoice_repository.list_payments(invoice.id)
