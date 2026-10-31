"""The database itself must reject bad data, whatever the services do."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    Customer,
    Discount,
    Invoice,
    InvoiceLine,
    Payment,
    Plan,
    Product,
    ProductVariant,
    QuotationTemplate,
    Subscription,
    SubscriptionLine,
    TemplateLine,
    User,
)
from app.models.enums import BillingPeriod, DiscountType, PaymentMethod

pytestmark = pytest.mark.usefixtures("app_context")

PERIOD_START = date(2026, 1, 1)


@pytest.fixture
def product(app):
    product = Product(name="Odoo Hosting", sales_price=Decimal("1000.00"))
    db.session.add(product)
    db.session.flush()
    return product


@pytest.fixture
def plan(app):
    plan = Plan(name="Monthly", billing_period=BillingPeriod.MONTHLY)
    db.session.add(plan)
    db.session.flush()
    return plan


@pytest.fixture
def subscription(app, plan):
    customer = Customer(name="Acme", email="billing@acme.test")
    db.session.add(customer)
    db.session.flush()
    subscription = Subscription(
        subscription_number="SUB-1", customer_id=customer.id, plan_id=plan.id
    )
    db.session.add(subscription)
    db.session.flush()
    return subscription


def make_invoice(subscription, number="INV-1", **overrides):
    values = {
        "invoice_number": number,
        "subscription_id": subscription.id,
        "customer_id": subscription.customer_id,
        "customer_snapshot": {"name": "Acme"},
        "period_start": PERIOD_START,
        "period_end": date(2026, 1, 31),
        "invoice_date": PERIOD_START,
        "due_date": date(2026, 1, 15),
    }
    values.update(overrides)
    return Invoice(**values)


def assert_rejected(*rows):
    db.session.add_all(rows)
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def make_user(email):
    return User(email=email, password_hash="x", full_name="Test", role="customer")


def test_user_email_is_stored_lowercase(app):
    user = make_user("  Mixed.Case@Example.COM ")
    db.session.add(user)
    db.session.flush()

    assert user.email == "mixed.case@example.com"


def test_user_email_is_unique_ignoring_case(app):
    db.session.add(make_user("same@example.com"))
    db.session.flush()

    assert_rejected(make_user("SAME@example.com"))


def test_database_rejects_uppercase_email_written_directly(app):
    statement = text(
        "INSERT INTO users (email, password_hash, full_name, role) "
        "VALUES ('UPPER@example.com', 'x', 'Test', 'customer')"
    )
    with pytest.raises(IntegrityError):
        db.session.execute(statement)


def test_invalid_role_is_rejected(app):
    user = make_user("role@example.com")
    user.role = "superuser"

    assert_rejected(user)


def test_only_staff_have_a_staff_function(app):
    customer = make_user("customer@example.com")
    customer.staff_function = "support"
    assert_rejected(customer)

    assert_rejected(
        User(email="staff@example.com", password_hash="x", full_name="T", role="staff")
    )


def test_second_invoice_for_the_same_period_is_rejected(subscription):
    db.session.add(make_invoice(subscription, "INV-1"))
    db.session.flush()

    assert_rejected(make_invoice(subscription, "INV-2"))


def test_invoice_for_the_next_period_is_accepted(subscription):
    db.session.add(make_invoice(subscription, "INV-1"))
    db.session.add(
        make_invoice(
            subscription,
            "INV-2",
            period_start=date(2026, 2, 1),
            period_end=date(2026, 2, 28),
            invoice_date=date(2026, 2, 1),
            due_date=date(2026, 2, 15),
        )
    )
    db.session.flush()


def test_amount_paid_cannot_exceed_total(subscription):
    assert_rejected(
        make_invoice(subscription, total=Decimal("100.00"), amount_paid=Decimal("100.01"))
    )


def test_active_subscription_needs_a_next_billing_date(subscription):
    subscription.status = "active"

    assert_rejected(subscription)


def test_plan_valid_to_cannot_precede_valid_from(app):
    assert_rejected(
        Plan(
            name="Bad dates",
            billing_period=BillingPeriod.MONTHLY,
            valid_from=date(2026, 2, 1),
            valid_to=date(2026, 1, 1),
        )
    )


def make_discount(**overrides):
    values = {
        "code": "SAVE10",
        "name": "Save 10",
        "discount_type": DiscountType.PERCENT,
        "value": Decimal("10.00"),
    }
    values.update(overrides)
    return Discount(**values)


def test_discount_valid_to_cannot_precede_valid_from(app):
    assert_rejected(
        make_discount(valid_from=date(2026, 2, 1), valid_to=date(2026, 1, 1))
    )


def test_discount_usage_count_cannot_exceed_limit(app):
    assert_rejected(make_discount(usage_limit=5, usage_count=6))


def test_discount_without_a_limit_allows_any_usage_count(app):
    db.session.add(make_discount(usage_limit=None, usage_count=1000))
    db.session.flush()


def test_percent_discount_cannot_exceed_100(app):
    assert_rejected(make_discount(value=Decimal("100.01")))


def test_subscription_line_quantity_must_be_positive(subscription, product):
    assert_rejected(
        SubscriptionLine(
            subscription_id=subscription.id,
            product_id=product.id,
            quantity=0,
            unit_price=Decimal("10.00"),
        )
    )


def test_template_line_quantity_must_be_positive(plan, product):
    template = QuotationTemplate(name="Standard", plan_id=plan.id, validity_days=30)
    db.session.add(template)
    db.session.flush()

    assert_rejected(
        TemplateLine(template_id=template.id, product_id=product.id, quantity=0)
    )


def test_invoice_line_quantity_must_be_positive(subscription):
    invoice = make_invoice(subscription)
    db.session.add(invoice)
    db.session.flush()

    assert_rejected(
        InvoiceLine(
            invoice_id=invoice.id,
            description="Hosting",
            quantity=0,
            unit_price=Decimal("10.00"),
            line_total=Decimal("0.00"),
        )
    )


def test_payment_amount_must_be_positive(subscription):
    invoice = make_invoice(subscription)
    db.session.add(invoice)
    db.session.flush()

    assert_rejected(
        Payment(
            invoice_id=invoice.id,
            method=PaymentMethod.CASH,
            amount=Decimal("0.00"),
            payment_date=PERIOD_START,
        )
    )


def test_duplicate_variant_is_rejected(product):
    def variant():
        return ProductVariant(
            product_id=product.id, attribute="Brand", value="Odoo", extra_price=Decimal("560.00")
        )

    db.session.add(variant())
    db.session.flush()

    assert_rejected(variant())


def test_required_indexes_are_declared(app):
    billing_index = next(
        index
        for index in Subscription.__table__.indexes
        if index.name == "ix_subscriptions_next_billing_date_active"
    )
    assert [column.name for column in billing_index.columns] == ["next_billing_date"]
    assert str(billing_index.dialect_options["postgresql"]["where"]) == "status = 'active'"

    invoice_indexes = {
        tuple(column.name for column in index.columns)
        for index in Invoice.__table__.indexes
    }
    assert ("status", "due_date") in invoice_indexes

    payment_indexes = {
        tuple(column.name for column in index.columns)
        for index in Payment.__table__.indexes
    }
    assert ("invoice_id",) in payment_indexes
