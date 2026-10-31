"""Queries for subscriptions, including customer scoping.

Reads take only_customer_id: None means every customer, so only pass None
after the service has established that the caller is staff or an admin.
"""
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Subscription, SubscriptionLine, subscription_number_seq
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
