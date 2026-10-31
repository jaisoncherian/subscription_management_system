"""Date arithmetic for billing periods."""
import calendar
from datetime import date, timedelta

from app.models.enums import BillingPeriod


def add_billing_period(start: date, period: str, interval: int = 1) -> date:
    """The date one billing period after `start`.

    Month ends are clamped: 31 January plus one month is 28 or 29 February.
    """
    if period == BillingPeriod.DAILY:
        return start + timedelta(days=interval)
    if period == BillingPeriod.WEEKLY:
        return start + timedelta(weeks=interval)
    months = interval * 12 if period == BillingPeriod.YEARLY else interval
    return _add_months(start, months)


def _add_months(start: date, months: int) -> date:
    month_index = start.year * 12 + (start.month - 1) + months
    year, month = month_index // 12, month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(start.day, last_day))
