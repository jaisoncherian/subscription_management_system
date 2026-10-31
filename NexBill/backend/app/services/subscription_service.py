"""Subscriptions: creation from a template, and the state machine."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from app.core import clock
from app.core.errors import Conflict, NotFound, ValidationFailed
from app.models import Subscription, SubscriptionLine, User
from app.models.enums import SubscriptionStatus as Status
from app.repositories import (
    audit_repository,
    catalog_repository,
    customer_repository,
    quotation_template_repository,
    subscription_repository,
    transaction,
)
from app.services import pricing_service
from app.services.access import customer_scope
from app.services.billing_periods import add_billing_period


def _start_quotation_validity(subscription: Subscription) -> None:
    # Validity runs from when the customer receives the quotation.
    if subscription.template:
        subscription.quotation_valid_until = clock.today() + timedelta(
            days=subscription.template.validity_days
        )


def _require_unexpired_quotation(subscription: Subscription) -> None:
    valid_until = subscription.quotation_valid_until
    if valid_until and valid_until < clock.today():
        raise Conflict("This quotation has expired.", code="quotation_expired")


def _start_billing(subscription: Subscription) -> None:
    start = subscription.start_date or clock.today()
    if subscription.expires_on and subscription.expires_on < start:
        raise Conflict(
            "This subscription would expire before it starts.",
            code="subscription_expired",
        )
    subscription.start_date = start
    subscription.next_billing_date = start


def _skip_paused_periods(subscription: Subscription) -> None:
    # Without this, the billing run would invoice the time spent paused.
    plan = subscription.plan
    next_date = subscription.next_billing_date
    while next_date < clock.today():
        next_date = add_billing_period(next_date, plan.billing_period, plan.billing_interval)
    subscription.next_billing_date = next_date


def _extend_expiry(subscription: Subscription) -> None:
    if subscription.expires_on is None:
        raise Conflict(
            "This subscription has no expiry date to extend.", code="no_expiry_date"
        )
    plan = subscription.plan
    subscription.expires_on = add_billing_period(
        subscription.expires_on, plan.billing_period, plan.billing_interval
    )


def _stamp_closed(subscription: Subscription) -> None:
    subscription.closed_at = datetime.now(timezone.utc)


@dataclass(frozen=True)
class Transition:
    sources: frozenset[Status]
    target: Status
    # A Plan column that must be true for this move to be allowed.
    plan_flag: str | None = None
    # Runs after the checks above. Raises to refuse the move, or updates dates.
    apply: Callable[[Subscription], None] | None = None


# The whole state machine. A move not listed here returns 409.
TRANSITIONS = {
    "send-quotation": Transition(
        frozenset({Status.DRAFT}), Status.QUOTATION, apply=_start_quotation_validity
    ),
    "confirm": Transition(
        frozenset({Status.QUOTATION}), Status.CONFIRMED, apply=_require_unexpired_quotation
    ),
    "activate": Transition(
        frozenset({Status.CONFIRMED}), Status.ACTIVE, apply=_start_billing
    ),
    "pause": Transition(frozenset({Status.ACTIVE}), Status.PAUSED, plan_flag="is_pausable"),
    "resume": Transition(
        frozenset({Status.PAUSED}), Status.ACTIVE, apply=_skip_paused_periods
    ),
    "renew": Transition(
        frozenset({Status.ACTIVE}), Status.ACTIVE, plan_flag="is_renewable", apply=_extend_expiry
    ),
    "close": Transition(
        frozenset({Status.ACTIVE, Status.PAUSED}),
        Status.CLOSED,
        plan_flag="is_closable",
        apply=_stamp_closed,
    ),
}


def create_from_template(
    actor: User,
    customer_id: int,
    template_id: int,
    start_date: date | None = None,
    expires_on: date | None = None,
    discount_id: int | None = None,
    notes: str | None = None,
) -> Subscription:
    customer = customer_repository.get_by_id(customer_id)
    if customer is None:
        raise ValidationFailed(fields={"customer_id": ["Unknown customer."]})

    template = quotation_template_repository.get_by_id(template_id)
    if template is None or not template.is_active:
        raise ValidationFailed(fields={"template_id": ["Unknown or inactive template."]})

    if expires_on and expires_on < (start_date or clock.today()):
        raise ValidationFailed(fields={"expires_on": ["Must not be before the start date."]})

    if discount_id is not None:
        discount = catalog_repository.get_discount(discount_id)
        if discount is None or not discount.is_active:
            raise ValidationFailed(fields={"discount_id": ["Unknown or inactive discount."]})

    _require_template_still_sellable(template)

    subscription = Subscription(
        subscription_number=subscription_repository.next_number(),
        customer_id=customer.id,
        plan_id=template.plan_id,
        template_id=template.id,
        discount_id=discount_id,
        created_by_user_id=actor.id,
        status=Status.DRAFT,
        quotation_valid_until=clock.today() + timedelta(days=template.validity_days),
        start_date=start_date,
        expires_on=expires_on,
        notes=notes,
        # Lines are copied, with today's price, so that later catalog or
        # template changes cannot alter an existing subscription.
        lines=[
            SubscriptionLine(
                product_id=line.product_id,
                variant_id=line.variant_id,
                tax_id=line.tax_id,
                quantity=line.quantity,
                unit_price=pricing_service.unit_price(line.product, line.variant),
            )
            for line in template.lines
        ],
    )
    subscription_repository.add(subscription)
    audit_repository.record(
        "subscription.created",
        "subscription",
        subscription.id,
        actor.id,
        {"template_id": template.id, "customer_id": customer.id},
    )
    transaction.commit()
    return subscription


def apply_action(actor: User, subscription_id: int, action: str) -> Subscription:
    transition = TRANSITIONS[action]
    subscription = subscription_repository.get_for_update(subscription_id)
    if subscription is None:
        raise NotFound("Subscription not found.")

    previous_status = subscription.status
    if previous_status not in transition.sources:
        raise Conflict(
            f"Cannot {action} a subscription that is {previous_status}.",
            code="invalid_transition",
        )
    if transition.plan_flag and not getattr(subscription.plan, transition.plan_flag):
        raise Conflict(
            f"The {subscription.plan.name} plan does not allow {action}.",
            code="action_not_allowed_by_plan",
        )
    if transition.apply:
        transition.apply(subscription)

    subscription.status = transition.target
    audit_repository.record(
        f"subscription.{action}",
        "subscription",
        subscription.id,
        actor.id,
        {"from": previous_status, "to": transition.target},
    )
    transaction.commit()
    return subscription


def get_subscription(viewer: User, subscription_id: int) -> Subscription:
    """Another customer's subscription looks exactly like one that does not exist."""
    subscription = subscription_repository.get_visible(
        subscription_id, customer_scope(viewer)
    )
    if subscription is None:
        raise NotFound("Subscription not found.")
    return subscription


def list_subscriptions(
    viewer: User, status: str | None, page: int, per_page: int
) -> tuple[list[Subscription], int]:
    return subscription_repository.list_visible(
        customer_scope(viewer), status, page, per_page
    )


def _require_template_still_sellable(template) -> None:
    plan = template.plan
    today = clock.today()
    if (
        not plan.is_active
        or (plan.valid_from and plan.valid_from > today)
        or (plan.valid_to and plan.valid_to < today)
    ):
        raise Conflict(f"The {plan.name} plan is not available.", code="plan_unavailable")

    for line in template.lines:
        unavailable = (
            not line.product.is_active
            or (line.variant and not line.variant.is_active)
            or (line.tax and not line.tax.is_active)
        )
        if unavailable:
            raise Conflict(
                f"{line.product.name} is no longer available. Update the template first.",
                code="catalog_item_inactive",
            )
        if line.quantity < plan.min_quantity:
            raise Conflict(
                f"The {plan.name} plan needs a quantity of at least {plan.min_quantity}. "
                "Update the template first.",
                code="below_plan_minimum",
            )
