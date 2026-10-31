"""Queries for subscriptions, including customer scoping.

Reads take only_customer_id: None means every customer, so only pass None
after the service has established that the caller is staff or an admin.
"""
from datetime import date

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Plan, Subscription, SubscriptionLine, subscription_number_seq
from app.models.enums import SubscriptionStatus
from app.repositories import sequences


def next_number() -> str:
    return f"SUB-{sequences.next_value(subscription_number_seq):06d}"


def add(subscription: Subscription) -> Subscription:
    db.session.add(subscription)
    db.session.flush()
    return subscription


def get_visible(subscription_id: int, only_customer_id: int | None) -> Subscription | None:
    query = db.select(Subscription).where(Subscription.id == subscription_id)
    if only_customer_id is not None:
        query = query.where(Subscription.customer_id == only_customer_id)
    return db.session.scalar(query)


def get_for_update(subscription_id: int) -> Subscription | None:
    """Lock the row, so that two simultaneous state changes cannot both apply."""
    return db.session.scalar(
        db.select(Subscription)
        .where(Subscription.id == subscription_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def lock_due_for_billing(
    today: date, batch_size: int, excluded_ids: set[int]
) -> list[Subscription]:
    """Lock the next batch that has a period to bill.

    SKIP LOCKED lets overlapping billing runs share the work instead of queueing.
    Periods starting after the expiry date are never billed.
    """
    query = (
        db.select(Subscription)
        .where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.next_billing_date <= today,
            db.or_(
                Subscription.expires_on.is_(None),
                Subscription.next_billing_date <= Subscription.expires_on,
            ),
        )
        .order_by(Subscription.next_billing_date, Subscription.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
        .execution_options(populate_existing=True)
    )
    if excluded_ids:
        query = query.where(Subscription.id.not_in(excluded_ids))
    return list(db.session.scalars(query))


def lock_expired_for_auto_close(
    today: date, batch_size: int, excluded_ids: set[int]
) -> list[Subscription]:
    query = (
        db.select(Subscription)
        .where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_on < today,
            Subscription.plan_id.in_(db.select(Plan.id).where(Plan.is_auto_close.is_(True))),
        )
        .order_by(Subscription.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
        .execution_options(populate_existing=True)
    )
    if excluded_ids:
        query = query.where(Subscription.id.not_in(excluded_ids))
    return list(db.session.scalars(query))


def list_visible(
    only_customer_id: int | None, status: str | None, page: int, per_page: int
) -> tuple[list[Subscription], int]:
    query = db.select(Subscription).order_by(Subscription.id.desc())
    if only_customer_id is not None:
        query = query.where(Subscription.customer_id == only_customer_id)
    if status is not None:
        query = query.where(Subscription.status == status)
    query = query.options(
        selectinload(Subscription.customer),
        selectinload(Subscription.plan),
        selectinload(Subscription.lines).selectinload(SubscriptionLine.product),
    )
    result = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return result.items, result.total
