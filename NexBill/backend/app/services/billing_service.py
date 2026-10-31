"""The billing run: turns due subscriptions into draft invoices.

Safe to run at any time, and more than once. Overlapping runs cannot bill a
period twice, because of row locks and UNIQUE(subscription_id, period_start).
"""
import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.core import clock
from app.models import Discount, Invoice, InvoiceLine, Subscription, SubscriptionLine
from app.models.enums import InvoiceStatus, SubscriptionStatus
from app.repositories import (
    audit_repository,
    discount_repository,
    invoice_repository,
    subscription_repository,
    transaction,
)
from app.services import pricing_service
from app.services.billing_periods import add_billing_period

logger = logging.getLogger(__name__)

BATCH_SIZE = 200
DUPLICATE_PERIOD_CONSTRAINT = "uq_invoices_subscription_id_period_start"


@dataclass
class BillingSummary:
    invoices_created: int = 0
    duplicates_skipped: int = 0
    subscriptions_closed: int = 0
    failures: int = 0


def run_billing(actor_user_id: int | None = None, today: date | None = None) -> dict:
    today = today or clock.today()
    summary = BillingSummary()
    failed_ids: set[int] = set()

    # A subscription behind by several periods stays due after each invoice, so
    # later batches pick it up again until it has caught up.
    while batch := subscription_repository.lock_due_for_billing(
        today, BATCH_SIZE, failed_ids
    ):
        for subscription in batch:
            _bill_one_period(subscription, today, actor_user_id, summary, failed_ids)
        transaction.commit()

    # Runs after billing, so that an expiring subscription gets its last invoices.
    while batch := subscription_repository.lock_expired_for_auto_close(
        today, BATCH_SIZE, failed_ids
    ):
        for subscription in batch:
            _auto_close(subscription, actor_user_id, summary)
        transaction.commit()

    result = asdict(summary)
    audit_repository.record("billing.run", "billing", actor_user_id=actor_user_id, details=result)
    transaction.commit()
    logger.info("billing run finished", extra={"context": result})
    return result


def _bill_one_period(
    subscription: Subscription,
    today: date,
    actor_user_id: int | None,
    summary: BillingSummary,
    failed_ids: set[int],
) -> None:
    # Taken now, because a rolled back savepoint expires the loaded object.
    subscription_id = subscription.id
    try:
        with transaction.savepoint():
            _create_invoice(subscription, today, actor_user_id)
        summary.invoices_created += 1
    except IntegrityError as error:
        if DUPLICATE_PERIOD_CONSTRAINT not in str(error.orig):
            _record_failure(subscription_id, summary, failed_ids)
            return
        logger.warning(
            "billing period already invoiced, skipping",
            extra={"context": {"subscription_id": subscription_id}},
        )
        summary.duplicates_skipped += 1
    except Exception:
        # One broken subscription must not stop everyone else being billed.
        _record_failure(subscription_id, summary, failed_ids)
        return

    # Also after a duplicate: that period is done, and this one must move on.
    subscription.next_billing_date = _next_period_start(subscription)


def _record_failure(
    subscription_id: int, summary: BillingSummary, failed_ids: set[int]
) -> None:
    logger.exception(
        "billing failed for subscription",
        extra={"context": {"subscription_id": subscription_id}},
    )
    summary.failures += 1
    failed_ids.add(subscription_id)


def _create_invoice(
    subscription: Subscription, today: date, actor_user_id: int | None
) -> Invoice:
    lines = subscription.lines
    discount = _claim_discount(subscription.discount, lines, today)
    priced = pricing_service.price_lines(lines, discount)

    period_start = subscription.next_billing_date
    payment_terms = timedelta(days=current_app.config["INVOICE_PAYMENT_TERMS_DAYS"])
    invoice = invoice_repository.add(
        Invoice(
            invoice_number=invoice_repository.next_number(),
            subscription_id=subscription.id,
            customer_id=subscription.customer_id,
            customer_snapshot=_customer_snapshot(subscription),
            status=InvoiceStatus.DRAFT,
            period_start=period_start,
            period_end=_next_period_start(subscription) - timedelta(days=1),
            invoice_date=today,
            due_date=today + payment_terms,
            subtotal=priced.subtotal,
            tax_total=priced.tax_total,
            discount_total=priced.discount_total,
            total=priced.total,
            lines=[
                InvoiceLine(
                    product_id=line.source.product_id,
                    discount_id=line.discount_id,
                    description=_describe(line.source),
                    quantity=line.source.quantity,
                    unit_price=line.source.unit_price,
                    tax_name=line.source.tax.name if line.source.tax else None,
                    tax_rate=line.tax_rate,
                    tax_amount=line.tax_amount,
                    discount_amount=line.discount_amount,
                    line_total=line.total,
                )
                for line in priced.lines
            ],
        )
    )
    audit_repository.record(
        "invoice.generated",
        "invoice",
        invoice.id,
        actor_user_id,
        {"subscription_id": subscription.id, "period_start": period_start.isoformat()},
    )
    return invoice


def _claim_discount(
    discount: Discount | None, lines: list[SubscriptionLine], today: date
) -> Discount | None:
    """The discount to apply, with one use already taken from it."""
    if discount is None or not pricing_service.is_discount_eligible(discount, lines, today):
        return None
    # Eligibility above used a value that may be stale. The claim is the real
    # check: if another run took the last use first, this invoice is full price.
    return discount if discount_repository.claim(discount) else None


def _next_period_start(subscription: Subscription) -> date:
    """Always counted from the old date, so that no period is ever skipped."""
    plan = subscription.plan
    return add_billing_period(
        subscription.next_billing_date,
        plan.billing_period,
        plan.billing_interval,
        anchor_day=subscription.start_date.day if subscription.start_date else None,
    )


def _customer_snapshot(subscription: Subscription) -> dict:
    customer = subscription.customer
    return {
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address_line1": customer.address_line1,
        "address_line2": customer.address_line2,
        "city": customer.city,
        "state": customer.state,
        "postal_code": customer.postal_code,
        "country": customer.country,
        "tax_identifier": customer.tax_identifier,
    }


def _describe(line: SubscriptionLine) -> str:
    if line.variant:
        return f"{line.product.name} ({line.variant.attribute}: {line.variant.value})"
    return line.product.name


def _auto_close(
    subscription: Subscription, actor_user_id: int | None, summary: BillingSummary
) -> None:
    subscription.status = SubscriptionStatus.CLOSED
    subscription.closed_at = datetime.now(timezone.utc)
    audit_repository.record(
        "subscription.auto_closed",
        "subscription",
        subscription.id,
        actor_user_id,
        {"expires_on": subscription.expires_on.isoformat()},
    )
    summary.subscriptions_closed += 1
