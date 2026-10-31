from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token
from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture
def portal_app():
    app = create_app("testing")
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    with app.app_context():
        User.__table__.create(db.engine)
        db.session.add_all(
            [
                User(id=101, email="portal-customer-1@example.test", password_hash="unused", full_name="Customer One", role="customer"),
                User(id=102, email="portal-customer-2@example.test", password_hash="unused", full_name="Customer Two", role="customer"),
                User(id=103, email="portal-staff@example.test", password_hash="unused", full_name="Portal Staff", role="staff", staff_function="support"),
            ]
        )
        db.session.flush()
        db.session.execute(text("CREATE TABLE customers (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL)"))
        db.session.execute(text("CREATE TABLE plans (id INTEGER PRIMARY KEY, price NUMERIC(12,2), billing_period VARCHAR(20))"))
        db.session.execute(
            text(
                """
                CREATE TABLE subscriptions (
                    id INTEGER PRIMARY KEY,
                    number VARCHAR(50) NOT NULL,
                    customer_id INTEGER NOT NULL,
                    plan_id INTEGER,
                    status VARCHAR(20) NOT NULL,
                    start_date DATE,
                    expiry_date DATE,
                    next_billing_date DATE
                )
                """
            )
        )
        db.session.execute(
            text(
                """
                CREATE TABLE invoices (
                    id INTEGER PRIMARY KEY,
                    number VARCHAR(50) NOT NULL,
                    subscription_id INTEGER,
                    customer_id INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    issue_date DATE,
                    due_date DATE,
                    subtotal NUMERIC(12,2),
                    tax_total NUMERIC(12,2),
                    discount_total NUMERIC(12,2),
                    total NUMERIC(12,2) NOT NULL
                )
                """
            )
        )
        db.session.execute(
            text(
                """
                CREATE TABLE payments (
                    id INTEGER PRIMARY KEY,
                    invoice_id INTEGER NOT NULL,
                    method VARCHAR(20),
                    amount NUMERIC(12,2) NOT NULL,
                    paid_on DATE
                )
                """
            )
        )

        db.session.execute(text("INSERT INTO customers (id, user_id) VALUES (1, 101), (2, 102)"))
        db.session.execute(text("INSERT INTO plans (id, price, billing_period) VALUES (1, 49.00, 'monthly'), (2, 129.00, 'yearly')"))
        db.session.execute(
            text(
                """
                INSERT INTO subscriptions (id, number, customer_id, plan_id, status, start_date, expiry_date, next_billing_date) VALUES
                    (1, 'SUB-100', 1, 1, 'active', '2025-01-01', '2026-01-01', '2025-02-01'),
                    (2, 'SUB-200', 1, 2, 'paused', '2025-03-01', '2026-03-01', '2025-04-01'),
                    (3, 'SUB-300', 2, 1, 'active', '2025-01-15', '2026-01-15', '2025-02-15')
                """
            )
        )
        db.session.execute(
            text(
                """
                INSERT INTO invoices (id, number, subscription_id, customer_id, status, issue_date, due_date, subtotal, tax_total, discount_total, total) VALUES
                    (1, 'INV-100', 1, 1, 'confirmed', '2025-01-05', '2025-01-20', 100.00, 0.00, 0.00, 100.00),
                    (2, 'INV-101', 1, 1, 'paid', '2025-02-05', '2025-02-20', 120.00, 0.00, 0.00, 120.00),
                    (3, 'INV-200', 2, 1, 'draft', '2025-03-05', '2025-03-20', 80.00, 0.00, 0.00, 80.00),
                    (4, 'INV-300', 2, 2, 'confirmed', '2025-04-05', '2025-04-20', 300.00, 0.00, 0.00, 300.00)
                """
            )
        )
        db.session.execute(
            text(
                """
                INSERT INTO payments (id, invoice_id, method, amount, paid_on) VALUES
                    (1, 1, 'card', 70.00, '2025-01-09'),
                    (2, 2, 'bank', 120.00, '2025-02-10')
                """
            )
        )
        db.session.commit()
        yield app
        db.session.execute(text("DROP TABLE IF EXISTS payments"))
        db.session.execute(text("DROP TABLE IF EXISTS invoices"))
        db.session.execute(text("DROP TABLE IF EXISTS subscriptions"))
        db.session.execute(text("DROP TABLE IF EXISTS plans"))
        db.session.execute(text("DROP TABLE IF EXISTS customers"))
        db.session.execute(text("DROP TABLE IF EXISTS users"))
        db.session.commit()
        db.session.remove()


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


def test_customer_sees_only_own_invoices(customer_client):
    resp = customer_client.get("/api/portal/invoices?page=1&page_size=10", headers=bearer_for_user(101))

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["total"] == 3
    assert {item["invoice_id"] for item in payload["items"]} == {1, 2, 3}
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
