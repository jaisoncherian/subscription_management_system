"""Repository layer for report queries."""
from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.extensions import db


def _is_postgres() -> bool:
    return db.session.bind is not None and db.session.bind.dialect.name == "postgresql"


def _today_expr() -> str:
    return "CURRENT_DATE" if _is_postgres() else "date('now')"


def _month_bucket(column_name: str) -> str:
    if _is_postgres():
        return f"date_trunc('month', {column_name})::date"
    return f"strftime('%Y-%m-01', {column_name})"


def _days_overdue_expr() -> str:
    if _is_postgres():
        return "(CURRENT_DATE - invoices.due_date)"
    return "(julianday(date('now')) - julianday(invoices.due_date))"


def _date_filter(field_name: str, *, table_alias: str = "") -> str:
    prefix = f"{table_alias}." if table_alias else ""
    return (
        f"(:date_from IS NULL OR {prefix}{field_name} >= :date_from) "
        f"AND (:date_to IS NULL OR {prefix}{field_name} <= :date_to)"
    )


def get_summary(date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    today_expr = _today_expr()
    sql = text(
        f"""
        WITH active_subscriptions AS (
            SELECT COUNT(*) AS active_subscriptions
            FROM subscriptions
            WHERE status = 'active'
        ),
        mrr AS (
            SELECT COALESCE(SUM(
                CASE
                    WHEN plans.billing_period = 'monthly' THEN subscription_lines.quantity * plans.price
                    WHEN plans.billing_period = 'yearly' THEN subscription_lines.quantity * plans.price / 12.0
                    WHEN plans.billing_period = 'weekly' THEN subscription_lines.quantity * plans.price * 52.0 / 12.0
                    WHEN plans.billing_period = 'daily' THEN subscription_lines.quantity * plans.price * 365.0 / 12.0
                    ELSE 0
                END
            ), 0) AS mrr
            FROM subscriptions
            JOIN subscription_lines ON subscription_lines.subscription_id = subscriptions.id
            JOIN plans ON plans.id = subscription_lines.plan_id
            WHERE subscriptions.status = 'active'
        ),
        revenue_collected AS (
            SELECT COALESCE(SUM(amount), 0) AS revenue_collected
            FROM payments
            WHERE (:date_from IS NULL OR paid_on >= :date_from)
              AND (:date_to IS NULL OR paid_on <= :date_to)
        ),
        outstanding AS (
            SELECT COALESCE(SUM(balance), 0) AS outstanding
            FROM (
                SELECT invoices.id,
                       invoices.total - COALESCE(SUM(payments.amount), 0) AS balance
                FROM invoices
                LEFT JOIN payments ON payments.invoice_id = invoices.id
                WHERE invoices.status = 'confirmed'
                  AND (:date_from IS NULL OR invoices.issue_date >= :date_from)
                  AND (:date_to IS NULL OR invoices.issue_date <= :date_to)
                GROUP BY invoices.id, invoices.total
            ) AS invoice_balances
        ),
        overdue_totals AS (
            SELECT COUNT(*) AS overdue_count
            FROM (
                SELECT invoices.id
                FROM invoices
                LEFT JOIN payments ON payments.invoice_id = invoices.id
                WHERE invoices.status = 'confirmed'
                  AND invoices.due_date < {today_expr}
                  AND (:date_from IS NULL OR invoices.due_date >= :date_from)
                  AND (:date_to IS NULL OR invoices.due_date <= :date_to)
                GROUP BY invoices.id, invoices.total
                HAVING invoices.total - COALESCE(SUM(payments.amount), 0) > 0
            ) AS overdue_invoices
        )
        SELECT
            a.active_subscriptions,
            m.mrr,
            r.revenue_collected,
            o.outstanding,
            ot.overdue_count
        FROM active_subscriptions AS a
        CROSS JOIN mrr AS m
        CROSS JOIN revenue_collected AS r
        CROSS JOIN outstanding AS o
        CROSS JOIN overdue_totals AS ot
        """
    )
    result = db.session.execute(sql, {"date_from": date_from, "date_to": date_to}).one()
    return {
        "active_subscriptions": int(result[0]),
        "mrr": float(result[1]),
        "revenue_collected": float(result[2]),
        "outstanding": float(result[3]),
        "overdue_count": int(result[4]),
    }


def get_revenue_by_period(date_from: str | None = None, date_to: str | None = None) -> list[dict[str, Any]]:
    invoiced_period = _month_bucket("issue_date")
    collected_period = _month_bucket("paid_on")
    sql = text(
        f"""
        WITH invoiced AS (
            SELECT {invoiced_period} AS period,
                   COALESCE(SUM(total), 0) AS invoiced
            FROM invoices
            WHERE (:date_from IS NULL OR issue_date >= :date_from)
              AND (:date_to IS NULL OR issue_date <= :date_to)
            GROUP BY {invoiced_period}
        ),
        collected AS (
            SELECT {collected_period} AS period,
                   COALESCE(SUM(amount), 0) AS collected
            FROM payments
            WHERE (:date_from IS NULL OR paid_on >= :date_from)
              AND (:date_to IS NULL OR paid_on <= :date_to)
            GROUP BY {collected_period}
        ),
        periods AS (
            SELECT period FROM invoiced
            UNION
            SELECT period FROM collected
        )
        SELECT p.period,
               COALESCE(i.invoiced, 0) AS invoiced,
               COALESCE(c.collected, 0) AS collected
        FROM periods AS p
        LEFT JOIN invoiced AS i ON i.period = p.period
        LEFT JOIN collected AS c ON c.period = p.period
        ORDER BY p.period
        """
    )
    rows = db.session.execute(sql, {"date_from": date_from, "date_to": date_to}).all()
    return [
        {
            "period": row[0].isoformat() if hasattr(row[0], "isoformat") else row[0],
            "invoiced": float(row[1]),
            "collected": float(row[2]),
        }
        for row in rows
    ]


def get_overdue_invoices(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict[str, Any]:
    today_expr = _today_expr()
    days_expr = _days_overdue_expr()
    sql = text(
        f"""
        WITH overdue_balances AS (
            SELECT
                invoices.id AS invoice_id,
                invoices.number,
                customers.id AS customer_id,
                invoices.due_date,
                invoices.total - COALESCE(SUM(payments.amount), 0) AS balance,
                {days_expr} AS days_overdue
            FROM invoices
            JOIN customers ON customers.id = invoices.customer_id
            LEFT JOIN payments ON payments.invoice_id = invoices.id
            WHERE invoices.status = 'confirmed'
              AND invoices.due_date < {today_expr}
              AND (:date_from IS NULL OR invoices.due_date >= :date_from)
              AND (:date_to IS NULL OR invoices.due_date <= :date_to)
            GROUP BY invoices.id, invoices.number, customers.id, invoices.due_date, invoices.total
            HAVING invoices.total - COALESCE(SUM(payments.amount), 0) > 0
        )
        SELECT invoice_id, number, customer_id, due_date, balance, days_overdue
        FROM overdue_balances
        ORDER BY due_date ASC, invoice_id ASC
        LIMIT :limit OFFSET :offset
        """
    )
    count_sql = text(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT invoices.id
            FROM invoices
            LEFT JOIN payments ON payments.invoice_id = invoices.id
            WHERE invoices.status = 'confirmed'
              AND invoices.due_date < {today_expr}
              AND (:date_from IS NULL OR invoices.due_date >= :date_from)
              AND (:date_to IS NULL OR invoices.due_date <= :date_to)
            GROUP BY invoices.id, invoices.total
            HAVING invoices.total - COALESCE(SUM(payments.amount), 0) > 0
        ) AS overdue
        """
    )

    params = {
        "date_from": date_from,
        "date_to": date_to,
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    rows = db.session.execute(sql, params).all()
    total = db.session.execute(count_sql, params).scalar_one()

    items = [
        {
            "invoice_id": row[0],
            "number": row[1],
            "customer": row[2],
            "due_date": row[3].isoformat() if hasattr(row[3], "isoformat") else row[3],
            "balance": float(row[4]),
            "days_overdue": int(row[5]),
        }
        for row in rows
    ]
    return {"items": items, "page": page, "page_size": page_size, "total": total}
