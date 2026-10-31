"""Seed demo data for Brightloop Software.

This module intentionally stays at the SQL layer so it works even before the
lead-owned models and migrations are merged. It follows the table contract in the
project docs and uses only the stdlib random module for repeatable demo data.
"""
from __future__ import annotations

import argparse
import os
import random
from datetime import date, timedelta
from typing import Any, Iterable

from sqlalchemy import text

from app import create_app
from app.extensions import db


BILLING_PERIODS = ["monthly", "yearly", "weekly", "daily"]
SUBSCRIPTION_STATUSES = ["active", "paused", "cancelled", "trialing", "past_due"]
INVOICE_STATUSES = ["draft", "confirmed", "paid", "overdue", "cancelled"]


def get_demo_passwords() -> dict[str, str]:
    """Return the env-based credentials for demo users without hardcoding secrets."""
    env_names = {
        "admin": "ADMIN_PASSWORD",
        "staff": "DEMO_STAFF_PASSWORD",
        "customer": "DEMO_CUSTOMER_PASSWORD",
    }
    missing = [name for name, key in env_names.items() if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Missing demo password env vars: " + ", ".join(missing)
        )
    return {kind: os.getenv(key) for kind, key in env_names.items()}


def seed_data(*, reset: bool = False, subscriptions: int = 10000) -> dict[str, int]:
    """Seed demo rows for plans, customers, subscriptions, invoices and payments."""
    passwords = get_demo_passwords()
    subscriptions = max(1, int(subscriptions))
    if reset:
        _reset_seed_tables()

    _ensure_seed_tables_exist()

    plan_rows = _build_plan_rows()
    if plan_rows:
        _bulk_insert("plans", ["id", "price", "billing_period"], plan_rows)

    customer_rows = _build_customer_rows()
    if customer_rows:
        _bulk_insert("customers", ["id", "user_id"], customer_rows)

    subscription_rows = _build_subscription_rows(subscriptions)
    if subscription_rows:
        _bulk_insert(
            "subscriptions",
            [
                "id",
                "number",
                "customer_id",
                "plan_id",
                "status",
                "start_date",
                "expiry_date",
                "next_billing_date",
            ],
            subscription_rows,
        )

    line_rows = _build_subscription_lines(subscription_rows)
    if line_rows:
        _bulk_insert(
            "subscription_lines",
            ["id", "subscription_id", "plan_id", "quantity"],
            line_rows,
        )

    invoice_rows = _build_invoice_rows(subscription_rows)
    if invoice_rows:
        _bulk_insert(
            "invoices",
            [
                "id",
                "number",
                "subscription_id",
                "customer_id",
                "status",
                "issue_date",
                "due_date",
                "subtotal",
                "tax_total",
                "discount_total",
                "total",
            ],
            invoice_rows,
        )

    payment_rows = _build_payment_rows(invoice_rows)
    if payment_rows:
        _bulk_insert(
            "payments",
            ["id", "invoice_id", "method", "amount", "paid_on"],
            payment_rows,
        )

    summary = {
        "customers": _count_rows("customers"),
        "plans": _count_rows("plans"),
        "subscriptions": _count_rows("subscriptions"),
        "subscription_lines": _count_rows("subscription_lines"),
        "invoices": _count_rows("invoices"),
        "payments": _count_rows("payments"),
    }
    db.session.commit()
    print(f"Seed summary: {summary}")
    print("Demo user passwords loaded from env vars:", passwords)
    return summary


def _reset_seed_tables() -> None:
    for table in ["payments", "invoices", "subscription_lines", "subscriptions", "customers", "plans"]:
        if _table_exists(table):
            db.session.execute(text(f"DELETE FROM {table}"))
    db.session.commit()


def _ensure_seed_tables_exist() -> None:
    for table, ddl in {
        "customers": "CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL)",
        "plans": "CREATE TABLE IF NOT EXISTS plans (id INTEGER PRIMARY KEY, price NUMERIC(12,2) NOT NULL, billing_period VARCHAR(20) NOT NULL)",
        "subscriptions": "CREATE TABLE IF NOT EXISTS subscriptions (id INTEGER PRIMARY KEY, number VARCHAR(50) NOT NULL, customer_id INTEGER NOT NULL, plan_id INTEGER, status VARCHAR(20) NOT NULL, start_date DATE, expiry_date DATE, next_billing_date DATE)",
        "subscription_lines": "CREATE TABLE IF NOT EXISTS subscription_lines (id INTEGER PRIMARY KEY, subscription_id INTEGER NOT NULL, plan_id INTEGER NOT NULL, quantity INTEGER NOT NULL)",
        "invoices": "CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY, number VARCHAR(50) NOT NULL, subscription_id INTEGER, customer_id INTEGER NOT NULL, status VARCHAR(20) NOT NULL, issue_date DATE, due_date DATE, subtotal NUMERIC(12,2), tax_total NUMERIC(12,2), discount_total NUMERIC(12,2), total NUMERIC(12,2) NOT NULL)",
        "payments": "CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, invoice_id INTEGER NOT NULL, method VARCHAR(20) NOT NULL, amount NUMERIC(12,2) NOT NULL, paid_on DATE NOT NULL)",
    }.items():
        if _table_exists(table):
            continue
        db.session.execute(text(ddl))
    db.session.commit()


def _table_exists(table_name: str) -> bool:
    result = db.session.execute(
        text(
            "SELECT 1 FROM information_schema.tables WHERE table_name = :table_name"
            if db.session.bind and db.session.bind.dialect.name == "postgresql"
            else "SELECT 1 FROM sqlite_master WHERE type='table' AND name = :table_name"
        ),
        {"table_name": table_name},
    ).first()
    return bool(result)


def _count_rows(table_name: str) -> int:
    row = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return int(row.scalar_one())


def _bulk_insert(table_name: str, columns: list[str], rows: list[dict[str, Any]], *, batch_size: int = 1000) -> None:
    if not rows:
        return
    placeholders = ", ".join(f":{column}" for column in columns)
    column_list = ", ".join(columns)
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        db.session.execute(
            text(f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"),
            batch,
        )


def _build_plan_rows() -> list[dict[str, Any]]:
    price_map = {
        "monthly": 49.0,
        "yearly": 499.0,
        "weekly": 12.0,
        "daily": 3.5,
    }
    return [
        {"id": idx + 1, "price": price_map[period], "billing_period": period}
        for idx, period in enumerate(BILLING_PERIODS)
    ]


def _build_customer_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(1, 101):
        rows.append({"id": idx, "user_id": 1000 + idx})
    return rows


def _build_subscription_rows(subscriptions: int) -> list[dict[str, Any]]:
    rng = random.Random(42)
    rows: list[dict[str, Any]] = []
    for idx in range(1, subscriptions + 1):
        customer_id = (idx % 100) + 1
        plan_id = (idx % len(BILLING_PERIODS)) + 1
        status = SUBSCRIPTION_STATUSES[idx % len(SUBSCRIPTION_STATUSES)]
        start_date = date(2024, 1, 1) + timedelta(days=(idx * 7) % 365)
        expiry_date = start_date + timedelta(days=365)
        next_billing_date = start_date + timedelta(days=30)
        row = {
            "id": idx,
            "number": f"SUB-{idx:06d}",
            "customer_id": customer_id,
            "plan_id": plan_id,
            "status": status,
            "start_date": start_date,
            "expiry_date": expiry_date,
            "next_billing_date": next_billing_date,
        }
        rows.append(row)
    return rows


def _build_subscription_lines(subscription_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    line_id = 1
    for sub in subscription_rows:
        line_count = 1 + (line_id % 3)
        for _ in range(line_count):
            rows.append(
                {
                    "id": line_id,
                    "subscription_id": sub["id"],
                    "plan_id": sub["plan_id"],
                    "quantity": 1 + (line_id % 5),
                }
            )
            line_id += 1
    return rows


def _build_invoice_rows(subscription_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    invoice_id = 1
    for sub in subscription_rows:
        for _ in range(1 + (invoice_id % 3)):
            issue_date = sub["start_date"] + timedelta(days=(invoice_id * 11) % 120)
            due_date = issue_date + timedelta(days=15)
            subtotal = 99.0 + ((invoice_id * 17) % 500)
            tax_total = subtotal * 0.1
            discount_total = 0.0 if invoice_id % 5 else 5.0
            total = round(subtotal + tax_total - discount_total, 2)
            status = INVOICE_STATUSES[invoice_id % len(INVOICE_STATUSES)]
            rows.append(
                {
                    "id": invoice_id,
                    "number": f"INV-{invoice_id:06d}",
                    "subscription_id": sub["id"],
                    "customer_id": sub["customer_id"],
                    "status": status,
                    "issue_date": issue_date,
                    "due_date": due_date,
                    "subtotal": subtotal,
                    "tax_total": tax_total,
                    "discount_total": discount_total,
                    "total": total,
                }
            )
            invoice_id += 1
    return rows


def _build_payment_rows(invoice_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    payment_id = 1
    for invoice in invoice_rows:
        if invoice["status"] == "draft":
            continue
        paid_amount = 0.0
        if invoice["status"] in {"paid", "overdue"}:
            paid_amount = float(invoice["total"])
        elif invoice["status"] == "confirmed":
            paid_amount = float(invoice["total"]) * 0.7
        if paid_amount > 0:
            rows.append(
                {
                    "id": payment_id,
                    "invoice_id": invoice["id"],
                    "method": "card" if payment_id % 2 else "bank",
                    "amount": round(paid_amount, 2),
                    "paid_on": invoice["issue_date"] + timedelta(days=5),
                }
            )
            payment_id += 1
    return rows


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed Brightloop demo data.")
    parser.add_argument("--reset", action="store_true", help="Delete existing seed rows before inserting.")
    parser.add_argument("--subscriptions", type=int, default=10000, help="Target number of subscriptions.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_cli().parse_args(list(argv) if argv is not None else None)
    app = create_app() if os.getenv("APP_ENV") else create_app("development")
    with app.app_context():
        summary = seed_data(reset=args.reset, subscriptions=args.subscriptions)
    print(f"Finished seeding: {summary}")
    return 0


def register_seed_data_cli(app) -> None:
    """Register a Flask CLI command when the app factory is ready to expose jobs."""
    import click

    @app.cli.command("seed-data")
    @click.option("--reset", is_flag=True, default=False, help="Delete existing demo rows before reseeding.")
    @click.option("--subscriptions", default=10000, show_default=True, type=int, help="Target subscription count.")
    def seed_data_command(reset: bool, subscriptions: int) -> None:
        with app.app_context():
            summary = seed_data(reset=reset, subscriptions=subscriptions)
        print(f"Seed summary: {summary}")


if __name__ == "__main__":
    raise SystemExit(main())
