"""Repository layer for customer portal queries."""
from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.extensions import db


def get_customer_id_for_user(user_id: Any) -> int | None:
    """Resolve the current customer's row from the JWT identity."""
    normalized_user_id = _coerce_user_id(user_id)
    if normalized_user_id is None:
        return None

    row = db.session.execute(
        text("SELECT id FROM customers WHERE user_id = :user_id LIMIT 1"),
        {"user_id": normalized_user_id},
    ).first()
    return int(row[0]) if row else None


def _coerce_user_id(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(stripped)
        except ValueError:
            return None
    return None


def list_customer_subscriptions(user_id: Any, *, page: int = 1, page_size: int = 25) -> dict[str, Any]:
    customer_id = get_customer_id_for_user(user_id)
    if customer_id is None:
        return {"items": [], "page": page, "page_size": page_size, "total": 0}

    count_sql = text("SELECT COUNT(*) FROM subscriptions WHERE customer_id = :customer_id")
    total = db.session.execute(count_sql, {"customer_id": customer_id}).scalar_one()

    # A very large page number would overflow OFFSET, and no rows exist that far along.
    offset = (page - 1) * page_size
    if offset >= total:
        return {"items": [], "page": page, "page_size": page_size, "total": total}

    rows = db.session.execute(
        text(
            """
            SELECT s.id,
                   s.subscription_number,
                   s.status,
                   s.start_date,
                   s.expires_on,
                   s.next_billing_date,
                   p.billing_period,
                   p.price,
                   p.name
            FROM subscriptions AS s
            LEFT JOIN plans AS p ON p.id = s.plan_id
            WHERE s.customer_id = :customer_id
            ORDER BY s.start_date DESC NULLS LAST, s.id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"customer_id": customer_id, "limit": page_size, "offset": offset},
    ).all()

    items = [
        {
            "subscription_id": row[0],
            "number": row[1],
            "status": row[2],
            "start_date": _format_date(row[3]),
            "expires_on": _format_date(row[4]),
            "next_billing_date": _format_date(row[5]),
            "billing_period": row[6],
            "price": _money_string(row[7]),
            "plan_name": row[8],
        }
        for row in rows
    ]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


def list_customer_invoices(user_id: Any, *, page: int = 1, page_size: int = 25) -> dict[str, Any]:
    customer_id = get_customer_id_for_user(user_id)
    if customer_id is None:
        return {"items": [], "page": page, "page_size": page_size, "total": 0}

    # Drafts are hidden from customers, the same as on GET /api/invoices.
    count_sql = text(
        "SELECT COUNT(*) FROM invoices WHERE customer_id = :customer_id AND status <> 'draft'"
    )
    total = db.session.execute(count_sql, {"customer_id": customer_id}).scalar_one()

    # A very large page number would overflow OFFSET, and no rows exist that far along.
    offset = (page - 1) * page_size
    if offset >= total:
        return {"items": [], "page": page, "page_size": page_size, "total": total}

    rows = db.session.execute(
        text(
            """
            SELECT i.id,
                   i.invoice_number,
                   i.status,
                   i.due_date,
                   i.total,
                   COALESCE(SUM(p.amount), 0) AS amount_paid
            FROM invoices AS i
            LEFT JOIN payments AS p ON p.invoice_id = i.id
            WHERE i.customer_id = :customer_id AND i.status <> 'draft'
            GROUP BY i.id, i.invoice_number, i.status, i.due_date, i.total, i.invoice_date
            ORDER BY i.invoice_date DESC, i.id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"customer_id": customer_id, "limit": page_size, "offset": offset},
    ).all()

    items = [
        {
            "invoice_id": row[0],
            "number": row[1],
            "status": row[2],
            "total": _money_string(row[4]),
            "amount_paid": _money_string(row[5]),
            "balance": _money_string((row[4] or 0) - (row[5] or 0)),
            "due_date": _format_date(row[3]),
        }
        for row in rows
    ]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


def _money_string(value: Any) -> str:
    if value is None:
        return "0.00"
    return f"{value:.2f}"


def _format_date(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
