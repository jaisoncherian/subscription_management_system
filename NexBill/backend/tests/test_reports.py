from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token
from sqlalchemy import text

from app import create_app
from app.extensions import db


@pytest.fixture
def reports_app():
    app = create_app("testing")
    with app.app_context():
        db.session.execute(
            text(
                """
                CREATE TABLE customers (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL
                )
                """
            )
        )
        db.session.execute(
            text(
                """
                CREATE TABLE plans (
                    id INTEGER PRIMARY KEY,
                    price NUMERIC(12,2) NOT NULL,
                    billing_period VARCHAR(20) NOT NULL
                )
                """
            )
        )
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
                CREATE TABLE subscription_lines (
                    id INTEGER PRIMARY KEY,
                    subscription_id INTEGER NOT NULL,
                    plan_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL
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
                    method VARCHAR(20) NOT NULL,
                    amount NUMERIC(12,2) NOT NULL,
                    paid_on DATE NOT NULL
                )
                """
            )
        )

        db.session.execute(
            text(
                """
                INSERT INTO customers (id, user_id) VALUES
                    (1, 101),
                    (2, 102),
                    (3, 103)
                """
            )
        )
        db.session.execute(
            text(
                """
                INSERT INTO plans (id, price, billing_period) VALUES
                    (1, 100.00, 'monthly'),
                    (2, 1200.00, 'yearly'),
                    (3, 20.00, 'weekly'),
                    (4, 7.00, 'daily')
                """
            )
        )
        db.session.execute(
            text(
                """
                INSERT INTO subscriptions (id, number, customer_id, plan_id, status, start_date, expiry_date, next_billing_date) VALUES
                    (1, 'SUB-001', 1, 1, 'active', '2025-01-01', '2026-01-01', '2025-02-01'),
                    (2, 'SUB-002', 1, 2, 'active', '2025-01-10', '2026-01-10', '2026-01-10'),
                    (3, 'SUB-003', 2, 3, 'active', '2025-02-01', '2025-08-01', '2025-02-08'),
                    (4, 'SUB-004', 2, 4, 'active', '2025-03-01', '2026-03-01', '2025-04-01'),
                    (5, 'SUB-005', 3, 4, 'cancelled', '2025-04-01', '2025-05-01', '2025-05-01')
                """
            )
        )
        db.session.execute(
            text(
                """
                INSERT INTO subscription_lines (id, subscription_id, plan_id, quantity) VALUES
                    (1, 1, 1, 2),
                    (2, 2, 2, 1),
                    (3, 3, 3, 3),
                    (4, 4, 4, 5),
                    (5, 5, 4, 1)
                """
            )
        )
        db.session.execute(
            text(
                """
                INSERT INTO invoices (id, number, subscription_id, customer_id, status, issue_date, due_date, subtotal, tax_total, discount_total, total) VALUES
                    (1, 'INV-001', 1, 1, 'confirmed', '2025-01-05', '2025-01-20', 500.00, 0.00, 0.00, 500.00),
                    (2, 'INV-002', 2, 1, 'confirmed', '2025-02-05', '2025-02-20', 220.00, 0.00, 0.00, 220.00),
                    (3, 'INV-003', 3, 2, 'cancelled', '2025-02-10', '2025-02-25', 120.00, 0.00, 0.00, 120.00),
                    (4, 'INV-004', 4, 2, 'confirmed', '2024-12-10', '2024-12-20', 300.00, 0.00, 0.00, 300.00),
                    (5, 'INV-005', 3, 2, 'confirmed', '2025-03-05', '2025-03-30', 90.00, 0.00, 0.00, 90.00)
                """
            )
        )
        db.session.execute(
            text(
                """
                INSERT INTO payments (id, invoice_id, method, amount, paid_on) VALUES
                    (1, 1, 'card', 300.00, '2025-01-10'),
                    (2, 2, 'bank', 200.00, '2025-02-06'),
                    (3, 4, 'card', 100.00, '2025-01-02'),
                    (4, 5, 'bank', 90.00, '2025-03-08')
                """
            )
        )
        db.session.commit()
        yield app
        db.session.execute(text("DROP TABLE IF EXISTS payments"))
        db.session.execute(text("DROP TABLE IF EXISTS invoices"))
        db.session.execute(text("DROP TABLE IF EXISTS subscription_lines"))
        db.session.execute(text("DROP TABLE IF EXISTS subscriptions"))
        db.session.execute(text("DROP TABLE IF EXISTS plans"))
        db.session.execute(text("DROP TABLE IF EXISTS customers"))
        db.session.commit()
        db.session.remove()


@pytest.fixture
def staff_client(reports_app):
    with reports_app.test_client() as client:
        yield client


def auth_header(role: str):
    token = create_access_token(identity=f"user-{role}", additional_claims={"roles": [role]})
    return {"Authorization": f"Bearer {token}"}


def test_summary_numbers_match_handbuilt_dataset(staff_client):
    response = staff_client.get("/api/reports/summary", headers=auth_header("admin"))

    assert response.status_code == 200
    data = response.get_json()
    assert data["active_subscriptions"] == 4
    assert data["mrr"] == 1624.5833333333333
    assert data["revenue_collected"] == 690.0
    assert data["outstanding"] == 420.0
    assert data["overdue_count"] == 3


def test_revenue_endpoint_groups_by_month(staff_client):
    response = staff_client.get(
        "/api/reports/revenue?group=month&date_from=2025-01-01&date_to=2025-12-31",
        headers=auth_header("staff"),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert any(item["period"] == "2025-01-01" and item["invoiced"] == 500.0 and item["collected"] == 400.0 for item in payload)
    assert any(item["period"] == "2025-02-01" and item["invoiced"] == 340.0 and item["collected"] == 200.0 for item in payload)


def test_overdue_excludes_paid_cancelled_and_not_due(staff_client):
    response = staff_client.get("/api/reports/overdue?page=1&page_size=10", headers=auth_header("staff"))

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == 3
    assert [item["invoice_id"] for item in payload["items"]] == [4, 1, 2]
    assert payload["items"][0]["balance"] == 200.0
    assert payload["items"][0]["days_overdue"] > 0


def test_invalid_date_range_returns_422(staff_client):
    response = staff_client.get(
        "/api/reports/summary?date_from=2025-02-01&date_to=2025-01-01",
        headers=auth_header("admin"),
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"


def test_customer_cannot_access_reports(staff_client):
    response = staff_client.get("/api/reports/summary", headers=auth_header("customer"))

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "forbidden"
