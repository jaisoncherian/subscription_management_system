"""Service layer for portal queries."""
from __future__ import annotations

from app.repositories import portal_repository


def list_customer_subscriptions(user_id, *, page: int = 1, page_size: int = 25):
    return portal_repository.list_customer_subscriptions(
        user_id,
        page=page,
        page_size=page_size,
    )


def list_customer_invoices(user_id, *, page: int = 1, page_size: int = 25):
    return portal_repository.list_customer_invoices(
        user_id,
        page=page,
        page_size=page_size,
    )
