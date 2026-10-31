"""The billing run. These need real savepoints and SKIP LOCKED, so PostgreSQL only."""
import threading
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import AuditLog, Customer, Discount, Invoice, Subscription
from app.services import billing_service, pricing_service
from app.services.billing_periods import add_billing_period
from helpers import (
    ApiClient,
    assert_error,
    make_active_subscription,
    make_admin,
    make_catalog,
    make_customer,
    make_staff,
    template_payload,
)

pytestmark = pytest.mark.postgres

TODAY = date.today()


def months_ago(months):
    day = TODAY.replace(day=min(TODAY.day, 28))
    index = day.year * 12 + day.month - 1 - months
    return date(index // 12, index % 12 + 1, day.day)


@pytest.fixture
def world(app):
    admin = make_admin(app)
    catalog = make_catalog(app, {"is_auto_close": True})
    template_id = admin.post(
        "/api/quotation-templates", template_payload(catalog)
    ).get_json()["id"]
    _, customer_id = make_customer(app)
    return {
        "app": app,
        "admin": admin,
        "catalog": catalog,
        "template_id": template_id,
        "customer_id": customer_id,
    }


def activate(world, **kwargs):
    return make_active_subscription(
        world["app"], world["admin"], world["customer_id"], world["template_id"], **kwargs
    )


def run(app, today=None):
    with app.app_context():
        return billing_service.run_billing(today=today)


def invoices_for(app, subscription_id):
    with app.app_context():
        rows = db.session.scalars(
            db.select(Invoice)
            .where(Invoice.subscription_id == subscription_id)
            .order_by(Invoice.period_start)
        ).all()
        return [
            {
                "number": row.invoice_number,
                "status": row.status,
                "period_start": row.period_start,
                "period_end": row.period_end,
                "due_date": row.due_date,
                "subtotal": row.subtotal,
                "discount_total": row.discount_total,
                "tax_total": row.tax_total,
                "total": row.total,
                "snapshot": row.customer_snapshot,
                "lines": [
                    {
                        "description": line.description,
                        "discount_id": line.discount_id,
                        "tax_name": line.tax_name,
                        "line_total": line.line_total,
                    }
                    for line in row.lines
                ],
            }
            for row in rows
        ]


def subscription_value(app, subscription_id, attribute):
    with app.app_context():
        return getattr(db.session.get(Subscription, subscription_id), attribute)


def make_discount(app, **overrides):
    values = {
        "code": "SAVE10",
        "name": "Save 10",
        "discount_type": "percent",
        "value": Decimal("10.00"),
    }
    values.update(overrides)
    with app.app_context():
        discount = Discount(**values)
        db.session.add(discount)
        db.session.commit()
        return discount.id


def discount_usage(app, discount_id):
    with app.app_context():
        return db.session.get(Discount, discount_id).usage_count


# Building the invoice


def test_due_subscription_gets_a_draft_invoice(world):
    subscription_id = activate(world)

    summary = run(world["app"])

    assert summary["invoices_created"] == 1
    invoice = invoices_for(world["app"], subscription_id)[0]
    assert invoice["status"] == "draft"
    assert invoice["number"].startswith("INV-")
    assert invoice["period_start"] == TODAY
    assert invoice["period_end"] == add_billing_period(TODAY, "monthly") - timedelta(days=1)
    assert invoice["due_date"] == TODAY + timedelta(days=15)


def test_invoice_totals_and_lines_include_variant_price_and_tax(world):
    subscription_id = activate(world)

    run(world["app"])

    invoice = invoices_for(world["app"], subscription_id)[0]
    # 2 x (1000 + 560) = 3120, plus 18% tax = 561.60
    assert invoice["subtotal"] == Decimal("3120.00")
    assert invoice["tax_total"] == Decimal("561.60")
    assert invoice["total"] == Decimal("3681.60")
    line = invoice["lines"][0]
    assert line["description"] == "Hosting (Brand: Odoo)"
    assert line["tax_name"] == "GST 18%"


def test_invoice_keeps_the_customer_as_they_were(world):
    subscription_id = activate(world)
    run(world["app"])
    with world["app"].app_context():
        db.session.get(Customer, world["customer_id"]).name = "New Name Ltd"
        db.session.commit()

    assert invoices_for(world["app"], subscription_id)[0]["snapshot"]["name"] == "Customer"


def test_only_active_due_subscriptions_are_billed(app, world):
    future = activate(world, start_date=TODAY + timedelta(days=5))
    paused_or_draft = world["admin"].post(
        "/api/subscriptions",
        {"customer_id": world["customer_id"], "template_id": world["template_id"]},
    ).get_json()["id"]

    summary = run(app)

    assert summary["invoices_created"] == 0
    assert invoices_for(app, future) == []
    assert invoices_for(app, paused_or_draft) == []


# No double billing


def test_running_twice_does_not_bill_twice(world):
    subscription_id = activate(world)

    first = run(world["app"])
    second = run(world["app"])

    assert first["invoices_created"] == 1
    assert second["invoices_created"] == 0
    assert len(invoices_for(world["app"], subscription_id)) == 1


def test_duplicate_period_is_skipped_and_the_date_still_moves_on(world):
    subscription_id = activate(world)
    run(world["app"])
    moved_on_to = subscription_value(world["app"], subscription_id, "next_billing_date")
    # Simulates a crash or manual edit that left the date behind.
    with world["app"].app_context():
        db.session.get(Subscription, subscription_id).next_billing_date = TODAY
        db.session.commit()

    summary = run(world["app"])

    assert summary["duplicates_skipped"] == 1
    assert summary["invoices_created"] == 0
    assert summary["failures"] == 0
    assert len(invoices_for(world["app"], subscription_id)) == 1
    assert subscription_value(world["app"], subscription_id, "next_billing_date") == moved_on_to


def test_duplicate_does_not_use_up_a_discount(world):
    discount_id = make_discount(world["app"], usage_limit=5)
    subscription_id = activate(world, discount_id=discount_id)
    run(world["app"])
    assert discount_usage(world["app"], discount_id) == 1
    with world["app"].app_context():
        db.session.get(Subscription, subscription_id).next_billing_date = TODAY
        db.session.commit()

    run(world["app"])

    assert discount_usage(world["app"], discount_id) == 1


def test_overlapping_runs_cannot_double_bill(app, world):
    ids = [activate(world) for _ in range(6)]
    results = []

    def worker(barrier):
        barrier.wait()
        results.append(run(app))

    barrier = threading.Barrier(4)
    threads = [threading.Thread(target=worker, args=(barrier,)) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sum(result["invoices_created"] for result in results) == 6
    assert sum(result["failures"] for result in results) == 0
    for subscription_id in ids:
        assert len(invoices_for(app, subscription_id)) == 1


# Catching up


def test_missed_periods_all_catch_up_with_none_skipped(world):
    start = months_ago(3)
    subscription_id = activate(world, start_date=start)

    summary = run(world["app"])

    assert summary["invoices_created"] == 4
    periods = [i["period_start"] for i in invoices_for(world["app"], subscription_id)]
    expected = [start]
    for _ in range(3):
        expected.append(add_billing_period(expected[-1], "monthly"))
    assert periods == expected
    assert subscription_value(world["app"], subscription_id, "next_billing_date") > TODAY


def test_periods_are_contiguous(world):
    subscription_id = activate(world, start_date=months_ago(2))

    run(world["app"])

    invoices = invoices_for(world["app"], subscription_id)
    for earlier, later in zip(invoices, invoices[1:]):
        assert earlier["period_end"] + timedelta(days=1) == later["period_start"]


def test_month_end_billing_does_not_drift(world):
    subscription_id = activate(world, start_date=date(2025, 1, 31))

    run(world["app"], today=date(2025, 4, 1))

    periods = [i["period_start"] for i in invoices_for(world["app"], subscription_id)]
    assert periods == [date(2025, 1, 31), date(2025, 2, 28), date(2025, 3, 31)]


def test_catching_up_over_many_batches(monkeypatch, world):
    monkeypatch.setattr(billing_service, "BATCH_SIZE", 2)
    ids = [activate(world, start_date=months_ago(1)) for _ in range(3)]

    summary = run(world["app"])

    assert summary["invoices_created"] == 6
    assert all(len(invoices_for(world["app"], i)) == 2 for i in ids)


def test_paused_subscription_is_not_billed_until_resumed(app, world):
    with app.app_context():
        from app.models import Plan

        db.session.get(Plan, world["catalog"]["plan_id"]).is_pausable = True
        db.session.commit()
    subscription_id = activate(world)
    world["admin"].post(f"/api/subscriptions/{subscription_id}/pause")

    assert run(app)["invoices_created"] == 0

    world["admin"].post(f"/api/subscriptions/{subscription_id}/resume")
    assert run(app)["invoices_created"] == 1


# Discounts


def test_discount_is_applied_and_claimed_once_per_invoice(world):
    discount_id = make_discount(world["app"])
    subscription_id = activate(world, discount_id=discount_id)

    run(world["app"])

    invoice = invoices_for(world["app"], subscription_id)[0]
    assert invoice["discount_total"] == Decimal("312.00")
    # (3120 - 312) x 18% = 505.44
    assert invoice["tax_total"] == Decimal("505.44")
    assert invoice["total"] == Decimal("3313.44")
    assert invoice["lines"][0]["discount_id"] == discount_id
    assert discount_usage(world["app"], discount_id) == 1


def test_usage_limit_holds_across_repeated_runs(world):
    discount_id = make_discount(world["app"], usage_limit=2)
    subscription_id = activate(world, start_date=months_ago(3), discount_id=discount_id)

    run(world["app"])
    run(world["app"])

    invoices = invoices_for(world["app"], subscription_id)
    assert [i["discount_total"] > 0 for i in invoices] == [True, True, False, False]
    assert discount_usage(world["app"], discount_id) == 2


def test_usage_limit_holds_across_subscriptions_in_one_run(world):
    discount_id = make_discount(world["app"], usage_limit=1)
    ids = [activate(world, discount_id=discount_id) for _ in range(3)]

    run(world["app"])

    discounted = [invoices_for(world["app"], i)[0]["discount_total"] > 0 for i in ids]
    assert sum(discounted) == 1
    assert discount_usage(world["app"], discount_id) == 1


def test_overlapping_runs_cannot_exceed_a_usage_limit(app, world):
    discount_id = make_discount(app, usage_limit=2)
    ids = [activate(world, discount_id=discount_id) for _ in range(6)]

    def worker(barrier):
        barrier.wait()
        run(app)

    barrier = threading.Barrier(4)
    threads = [threading.Thread(target=worker, args=(barrier,)) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert discount_usage(app, discount_id) == 2
    discounted = sum(invoices_for(app, i)[0]["discount_total"] > 0 for i in ids)
    assert discounted == 2


def test_simultaneous_claims_on_the_last_use_give_exactly_one_win(app):
    from app.repositories import discount_repository

    discount_id = make_discount(app, usage_limit=1)
    wins = []

    def worker(barrier):
        with app.app_context():
            discount = db.session.get(Discount, discount_id)
            barrier.wait()
            won = discount_repository.claim(discount)
            db.session.commit()
            wins.append(won)

    barrier = threading.Barrier(5)
    threads = [threading.Thread(target=worker, args=(barrier,)) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sum(wins) == 1
    assert discount_usage(app, discount_id) == 1


def test_ineligible_discount_is_not_claimed(world):
    discount_id = make_discount(world["app"], min_purchase=Decimal("999999.00"))
    subscription_id = activate(world, discount_id=discount_id)

    run(world["app"])

    assert invoices_for(world["app"], subscription_id)[0]["discount_total"] == Decimal("0.00")
    assert discount_usage(world["app"], discount_id) == 0


# Expiry and auto-close


def test_expired_auto_close_subscription_gets_last_invoices_then_closes(world):
    start = months_ago(3)
    expiry = add_billing_period(start, "monthly") + timedelta(days=3)
    subscription_id = activate(world, start_date=start, expires_on=expiry)

    summary = run(world["app"])

    assert summary["invoices_created"] == 2
    assert summary["subscriptions_closed"] == 1
    assert subscription_value(world["app"], subscription_id, "status") == "closed"
    assert subscription_value(world["app"], subscription_id, "closed_at") is not None


def test_auto_close_waits_until_after_the_expiry_date(world):
    subscription_id = activate(world, expires_on=TODAY)

    assert run(world["app"])["subscriptions_closed"] == 0
    assert subscription_value(world["app"], subscription_id, "status") == "active"


def test_expired_subscription_closes_even_when_nothing_is_due(world):
    subscription_id = activate(world, start_date=TODAY + timedelta(days=1))
    with world["app"].app_context():
        subscription = db.session.get(Subscription, subscription_id)
        subscription.start_date = TODAY - timedelta(days=9)
        subscription.next_billing_date = TODAY + timedelta(days=20)
        subscription.expires_on = TODAY - timedelta(days=1)
        db.session.commit()

    summary = run(world["app"])

    assert summary["invoices_created"] == 0
    assert summary["subscriptions_closed"] == 1


def test_plan_without_auto_close_stays_active_and_stops_billing(app, world):
    with app.app_context():
        from app.models import Plan

        db.session.get(Plan, world["catalog"]["plan_id"]).is_auto_close = False
        db.session.commit()
    start = months_ago(2)
    subscription_id = activate(
        world, start_date=start, expires_on=start + timedelta(days=3)
    )

    summary = run(app)

    assert summary["invoices_created"] == 1
    assert summary["subscriptions_closed"] == 0
    assert subscription_value(app, subscription_id, "status") == "active"


# One bad subscription


def test_one_failure_does_not_stop_the_others(monkeypatch, world):
    bad = activate(world)
    good = activate(world)
    real_create = billing_service._create_invoice

    def create(subscription, today, actor_user_id):
        if subscription.id == bad:
            raise RuntimeError("boom")
        return real_create(subscription, today, actor_user_id)

    monkeypatch.setattr(billing_service, "_create_invoice", create)

    summary = run(world["app"])

    assert summary["failures"] == 1
    assert summary["invoices_created"] == 1
    assert invoices_for(world["app"], good)
    assert invoices_for(world["app"], bad) == []
    # Not moved on, so that the next run tries that period again.
    assert subscription_value(world["app"], bad, "next_billing_date") == TODAY


def test_failed_subscription_is_retried_by_the_next_run(monkeypatch, world):
    subscription_id = activate(world)

    def boom(*_args):
        raise RuntimeError("boom")

    with monkeypatch.context() as patch:
        patch.setattr(billing_service, "_create_invoice", boom)
        assert run(world["app"])["failures"] == 1

    assert run(world["app"])["invoices_created"] == 1
    assert len(invoices_for(world["app"], subscription_id)) == 1


# Entry points


def test_post_billing_run_is_admin_only(app, world):
    activate(world)
    staff = make_staff(app)
    customer, _ = make_customer(app, "other@example.com", "Other")

    assert_error(staff.post("/api/billing/run"), 403, "forbidden")
    assert_error(customer.post("/api/billing/run"), 403, "forbidden")
    assert_error(ApiClient(app).post("/api/billing/run"), 401, "unauthorized")

    response = world["admin"].post("/api/billing/run")
    assert response.status_code == 200
    assert response.get_json() == {
        "invoices_created": 1,
        "duplicates_skipped": 0,
        "subscriptions_closed": 0,
        "failures": 0,
    }


def test_flask_run_billing_command(app, world):
    activate(world)

    result = app.test_cli_runner().invoke(args=["run-billing"])

    assert result.exit_code == 0
    assert "Invoices created: 1" in result.output


def test_run_is_recorded_in_the_audit_log(app, world):
    world["admin"].post("/api/billing/run")

    with app.app_context():
        entry = db.session.scalar(db.select(AuditLog).where(AuditLog.action == "billing.run"))
        assert entry is not None
        assert entry.details["failures"] == 0


def test_pricing_service_stays_consistent_with_invoices(world):
    subscription_id = activate(world)
    run(world["app"])

    with world["app"].app_context():
        subscription = db.session.get(Subscription, subscription_id)
        priced = pricing_service.price_lines(subscription.lines)
    assert invoices_for(world["app"], subscription_id)[0]["total"] == priced.total
