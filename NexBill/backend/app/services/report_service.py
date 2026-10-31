"""Service layer for reporting queries."""
from __future__ import annotations

from app.repositories import report_repository


def get_summary(date_from: str | None = None, date_to: str | None = None):
    return report_repository.get_summary(date_from=date_from, date_to=date_to)


def get_revenue_by_period(date_from: str | None = None, date_to: str | None = None, group: str = "month"):
    if group != "month":
        raise ValueError("Only monthly grouping is supported currently.")
    return report_repository.get_revenue_by_period(date_from=date_from, date_to=date_to)


def get_overdue_invoices(date_from: str | None = None, date_to: str | None = None, page: int = 1, page_size: int = 25):
    return report_repository.get_overdue_invoices(
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
