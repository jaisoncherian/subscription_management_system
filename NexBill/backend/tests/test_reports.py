from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import (
    Customer,
    Invoice,
    Payment,
    Plan,
    Product,
    Subscription,
    SubscriptionLine,
)
from app.models.user import User


@pytest.fixture
def reports_app(app):
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    with app.app_context():
        db.session.add_all(
            [
                User(id=201, email="reports-admin@example.test", password_hash="unused", full_name="Reports Admin", role="admin"),
                User(id=202, email="reports-staff@example.test", password_hash="unused", full_name="Reports Staff", role="staff", staff_function="finance_lead"),
                User(id=203, email="reports-customer@example.test", password_hash="unused", full_name="Reports Customer", role="customer"),
                Customer(id=1, name="Customer One", email="one@example.test"),
                Customer(id=2, name="Customer Two", email="two@example.test"),
                Customer(id=3, name="Customer Three", email="three@example.test"),
                Plan(id=1, name="Monthly", billing_period="monthly"),
                Plan(id=2, name="Yearly", billing_period="yearly"),
                Plan(id=3, name="Weekly", billing_period="weekly"),
                Plan(id=4, name="Daily", billing_period="daily"),
                Product(id=1, name="Hosting", sales_price=Decimal("0.00")),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                _subscription(1, 1, 1, "active", "2025-01-01", "2026-01-01", "2025-02-01"),
                _subscription(2, 1, 2, "active", "2025-01-10", "2026-01-10", "2026-01-10"),
                _subscription(3, 2, 3, "active", "2025-02-01", "2025-08-01", "2025-02-08"),
                _subscription(4, 2, 4, "active", "2025-03-01", "2026-03-01", "2025-04-01"),
                _subscription(5, 3, 4, "closed", "2025-04-01", "2025-05-01", "2025-05-01"),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                _line(1, 1, 2, "100.00"),
                _line(2, 2, 1, "1200.00"),
                _line(3, 3, 3, "20.00"),
                _line(4, 4, 5, "7.00"),
                _line(5, 5, 1, "7.00"),
                _invoice(1, "INV-001", 1, 1, "confirmed", "2025-01-05", "2025-01-20", "500.00", "300.00"),
                _invoice(2, "INV-002", 2, 1, "confirmed", "2025-02-05", "2025-02-20", "220.00", "200.00"),
                _invoice(3, "INV-003", 3, 2, "cancelled", "2025-02-10", "2025-02-25", "120.00", "0.00"),
                _invoice(4, "INV-004", 4, 2, "confirmed", "2024-12-10", "2024-12-20", "300.00", "100.00"),
                _invoice(5, "INV-005", 3, 2, "confirmed", "2025-03-05", "2025-03-30", "90.00", "90.00"),
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                _payment(1, 1, "card", "300.00", "2025-01-10"),
                _payment(2, 2, "bank_transfer", "200.00", "2025-02-06"),
                _payment(3, 4, "card", "100.00", "2025-01-02"),
                _payment(4, 5, "bank_transfer", "90.00", "2025-03-08"),
            ]
        )
        db.session.commit()
        yield app


def _subscription(id, customer_id, plan_id, status, start, expires, next_billing):
    return Subscription(
        id=id,
        subscription_number=f"SUB-00{id}",
        customer_id=customer_id,
        plan_id=plan_id,
        status=status,
        start_date=date.fromisoformat(start),
        expires_on=date.fromisoformat(expires),
        next_billing_date=date.fromisoformat(next_billing),
    )


def _line(id, subscription_id, quantity, unit_price):
    return SubscriptionLine(
        id=id,
        subscription_id=subscription_id,
        product_id=1,
        quantity=quantity,
        unit_price=Decimal(unit_price),
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


def _payment(id, invoice_id, method, amount, payment_date):
    return Payment(
        id=id,
        invoice_id=invoice_id,
        method=method,
        amount=Decimal(amount),
        payment_date=date.fromisoformat(payment_date),
    )


@pytest.fixture
def staff_client(reports_app):
    with reports_app.test_client() as client:
        yield client


def auth_header(role: str):
    user_id = {"admin": 201, "staff": 202, "customer": 203}[role]
    token = create_access_token(identity=str(user_id), additional_claims={"roles": [role]})
    return {"Authorization": f"Bearer {token}"}


def test_summary_numbers_match_handbuilt_dataset(staff_client):
    response = staff_client.get("/api/reports/summary", headers=auth_header("admin"))

    assert response.status_code == 200
    data = response.get_json()
    assert data["active_subscriptions"] == 4
    assert data["mrr"] == "1624.58"
    assert data["revenue_collected"] == "690.00"
    assert data["outstanding"] == "420.00"
    assert data["overdue_count"] == 3


def test_revenue_endpoint_groups_by_month(staff_client):
    response = staff_client.get(
        "/api/reports/revenue?group=month&date_from=2025-01-01&date_to=2025-12-31",
        headers=auth_header("staff"),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert any(item["period"] == "2025-01-01" and item["invoiced"] == "500.00" and item["collected"] == "400.00" for item in payload)
    assert any(item["period"] == "2025-02-01" and item["invoiced"] == "220.00" and item["collected"] == "200.00" for item in payload)


def test_overdue_excludes_paid_cancelled_and_not_due(staff_client):
    response = staff_client.get("/api/reports/overdue?page=1&page_size=10", headers=auth_header("staff"))

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == 3
    assert [item["invoice_id"] for item in payload["items"]] == [4, 1, 2]
    assert payload["items"][0]["balance"] == "200.00"
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


def test_summary_with_a_date_range_runs_on_the_real_schema(staff_client):
    response = staff_client.get(
        "/api/reports/summary?date_from=2025-01-01&date_to=2025-01-31",
        headers=auth_header("admin"),
    )

    assert response.status_code == 200
    assert response.get_json()["revenue_collected"] == "400.00"


@pytest.mark.parametrize(
    "query", ["page=0", "page=-1", "page_size=0", "page_size=101"]
)
def test_invalid_pagination_returns_422(staff_client, query):
    response = staff_client.get(f"/api/reports/overdue?{query}", headers=auth_header("staff"))

    assert response.status_code == 422


def test_unknown_revenue_group_returns_422(staff_client):
    response = staff_client.get("/api/reports/revenue?group=year", headers=auth_header("staff"))

    assert response.status_code == 422


def test_enormous_page_number_does_not_overflow_the_database(staff_client):
    response = staff_client.get(f"/api/reports/overdue?page={10**30}", headers=auth_header("staff"))

    assert response.status_code == 200
    assert response.get_json()["items"] == []
