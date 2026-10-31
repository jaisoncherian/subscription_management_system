from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Customer, Invoice, Payment, Plan, Subscription
from app.models.user import User


@pytest.fixture
def portal_app(app):
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    with app.app_context():
        db.session.add_all(
            [
                User(id=101, email="portal-customer-1@example.test", password_hash="unused", full_name="Customer One", role="customer"),
                User(id=102, email="portal-customer-2@example.test", password_hash="unused", full_name="Customer Two", role="customer"),
                User(id=103, email="portal-staff@example.test", password_hash="unused", full_name="Portal Staff", role="staff", staff_function="support"),
                Plan(id=1, name="Monthly", price=Decimal("49.00"), billing_period="monthly"),
                Plan(id=2, name="Yearly", price=Decimal("129.00"), billing_period="yearly"),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                Customer(id=1, user_id=101, name="Customer One", email="portal-customer-1@example.test"),
                Customer(id=2, user_id=102, name="Customer Two", email="portal-customer-2@example.test"),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                _subscription(1, "SUB-100", 1, 1, "active", "2025-01-01", "2026-01-01", "2025-02-01"),
                _subscription(2, "SUB-200", 1, 2, "paused", "2025-03-01", "2026-03-01", "2025-04-01"),
                _subscription(3, "SUB-300", 2, 1, "active", "2025-01-15", "2026-01-15", "2025-02-15"),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                _invoice(1, "INV-100", 1, 1, "confirmed", "2025-01-05", "2025-01-20", "100.00", "70.00"),
                _invoice(2, "INV-101", 1, 1, "paid", "2025-02-05", "2025-02-20", "120.00", "120.00"),
                _invoice(3, "INV-200", 2, 1, "draft", "2025-03-05", "2025-03-20", "80.00", "0.00"),
                _invoice(4, "INV-300", 2, 2, "confirmed", "2025-04-05", "2025-04-20", "300.00", "0.00"),
                _invoice(5, "INV-102", 1, 1, "confirmed", "2025-03-05", "2025-03-20", "50.00", "0.00"),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                Payment(id=1, invoice_id=1, method="card", amount=Decimal("70.00"), payment_date=date(2025, 1, 9)),
                Payment(id=2, invoice_id=2, method="bank_transfer", amount=Decimal("120.00"), payment_date=date(2025, 2, 10)),
            ]
        )
        db.session.commit()
        yield app


def _subscription(id, number, customer_id, plan_id, status, start, expires, next_billing):
    return Subscription(
        id=id,
        subscription_number=number,
        customer_id=customer_id,
        plan_id=plan_id,
        status=status,
        start_date=date.fromisoformat(start),
        expires_on=date.fromisoformat(expires),
        next_billing_date=date.fromisoformat(next_billing),
    )


def _invoice(id, number, subscription_id, customer_id, status, invoice_date, due_date, total, paid):
    return Invoice(
        id=id,
        invoice_number=number,
        subscription_id=subscription_id,
        customer_id=customer_id,
        customer_snapshot={"name": "Snapshot"},
        status=status,
        period_start=date.fromisoformat(invoice_date),
        period_end=date.fromisoformat(invoice_date),
        invoice_date=date.fromisoformat(invoice_date),
        due_date=date.fromisoformat(due_date),
        subtotal=Decimal(total),
        total=Decimal(total),
        amount_paid=Decimal(paid),
    )


@pytest.fixture
def customer_client(portal_app):
    with portal_app.test_client() as client:
        yield client


def bearer_for_user(user_id: int, role: str = "customer"):
    if role == "staff":
        user_id = 103
    token = create_access_token(identity=str(user_id), additional_claims={"roles": [role]})
    return {"Authorization": f"Bearer {token}"}


def test_customer_sees_only_own_subscriptions(customer_client):
    resp = customer_client.get("/api/portal/subscriptions?page=1&page_size=10", headers=bearer_for_user(101))

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["total"] == 2
    assert [item["subscription_id"] for item in payload["items"]] == [2, 1]
    assert all(item["number"].startswith("SUB-") for item in payload["items"])


def test_customer_sees_only_own_invoices_without_drafts(customer_client):
    resp = customer_client.get("/api/portal/invoices?page=1&page_size=10", headers=bearer_for_user(101))

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["total"] == 3
    assert {item["invoice_id"] for item in payload["items"]} == {1, 2, 5}
    item = next(item for item in payload["items"] if item["invoice_id"] == 1)
    assert item["status"] == "confirmed"
    assert item["total"] == "100.00"
    assert item["amount_paid"] == "70.00"
    assert item["balance"] == "30.00"
    assert item["due_date"] == "2025-01-20"


def test_staff_is_forbidden_on_portal(customer_client):
    resp = customer_client.get("/api/portal/subscriptions", headers=bearer_for_user(101, role="staff"))

    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "forbidden"


def test_portal_pagination_uses_server_side_total(customer_client):
    resp = customer_client.get("/api/portal/invoices?page=1&page_size=2", headers=bearer_for_user(101))

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert payload["total"] == 3
    assert len(payload["items"]) == 2


@pytest.mark.parametrize("query", ["page=0", "page=-1", "page_size=0", "page_size=101"])
def test_invalid_pagination_returns_422(customer_client, query):
    resp = customer_client.get(f"/api/portal/invoices?{query}", headers=bearer_for_user(101))

    assert resp.status_code == 422
