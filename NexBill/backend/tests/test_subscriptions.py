"""Subscriptions from templates, the state machine, and customer scoping."""
from datetime import date, timedelta

import pytest

from app.extensions import db
from app.models import AuditLog, Customer, Plan, Product, Subscription, User
from app.services.billing_periods import add_billing_period
from helpers import (
    ApiClient,
    assert_error,
    make_admin,
    make_catalog,
    make_customer,
    make_staff,
    template_payload,
)

URL = "/api/subscriptions"
TODAY = date.today()


@pytest.fixture
def world(app):
    """An admin, a catalog, a template and a customer."""
    admin = make_admin(app)
    catalog = make_catalog(
        app, {"is_pausable": True, "is_renewable": True, "is_closable": True}
    )
    template_id = admin.post(
        "/api/quotation-templates", template_payload(catalog)
    ).get_json()["id"]
    customer, customer_id = make_customer(app)
    return {
        "admin": admin,
        "catalog": catalog,
        "template_id": template_id,
        "customer": customer,
        "customer_id": customer_id,
    }


def create(world, **overrides):
    return world["admin"].post(
        URL,
        {"customer_id": world["customer_id"], "template_id": world["template_id"], **overrides},
    )


def create_id(world, **overrides):
    response = create(world, **overrides)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def act(world, subscription_id, action):
    return world["admin"].post(f"{URL}/{subscription_id}/{action}")


def move_to(world, subscription_id, *actions):
    for action in actions:
        response = act(world, subscription_id, action)
        assert response.status_code == 200, (action, response.get_json())


TO_ACTIVE = ("send-quotation", "confirm", "activate")


def update_subscription(app, subscription_id, **values):
    with app.app_context():
        subscription = db.session.get(Subscription, subscription_id)
        for key, value in values.items():
            setattr(subscription, key, value)
        db.session.commit()


def update_plan(app, world, **values):
    with app.app_context():
        plan = db.session.get(Plan, world["catalog"]["plan_id"])
        for key, value in values.items():
            setattr(plan, key, value)
        db.session.commit()


# Creating from a template


def test_create_copies_plan_lines_and_validity_from_the_template(world):
    response = create(world)

    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "draft"
    assert body["plan_id"] == world["catalog"]["plan_id"]
    assert body["template_id"] == world["template_id"]
    assert body["customer_name"] == "Customer"
    assert body["quotation_valid_until"] == (TODAY + timedelta(days=30)).isoformat()
    line = body["lines"][0]
    assert line["product_id"] == world["catalog"]["product_id"]
    assert line["variant_id"] == world["catalog"]["variant_id"]
    assert line["tax_id"] == world["catalog"]["tax_id"]
    assert line["quantity"] == 2


def test_unit_price_is_the_base_price_plus_the_variant_extra(world):
    assert create(world).get_json()["lines"][0]["unit_price"] == "1560.00"


def test_subscription_numbers_come_from_the_sequence_and_differ(world):
    first = create(world).get_json()["subscription_number"]
    second = create(world).get_json()["subscription_number"]

    assert first.startswith("SUB-") and len(first) == 10
    assert int(second[4:]) == int(first[4:]) + 1


def test_later_catalog_and_template_changes_do_not_touch_a_subscription(app, world):
    subscription_id = create_id(world)
    with app.app_context():
        db.session.get(Product, world["catalog"]["product_id"]).sales_price = 9999
        db.session.commit()
    new_lines = [{"product_id": world["catalog"]["other_product_id"], "quantity": 9}]
    world["admin"].put(
        f"/api/quotation-templates/{world['template_id']}",
        template_payload(world["catalog"], lines=new_lines),
    )

    line = world["admin"].get(f"{URL}/{subscription_id}").get_json()["lines"][0]

    assert line["unit_price"] == "1560.00"
    assert line["quantity"] == 2


def test_only_staff_and_admins_can_create(app, world):
    staff = make_staff(app)
    payload = {"customer_id": world["customer_id"], "template_id": world["template_id"]}

    assert staff.post(URL, payload).status_code == 201
    assert_error(world["customer"].post(URL, payload), 403, "forbidden")
    assert_error(ApiClient(app).post(URL, payload), 401, "unauthorized")


@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"customer_id": 99999}, "customer_id"),
        ({"template_id": 99999}, "template_id"),
        ({"discount_id": 99999}, "discount_id"),
        ({"customer_id": "1"}, "customer_id"),
        ({"start_date": "not-a-date"}, "start_date"),
        ({"expires_on": (TODAY - timedelta(days=1)).isoformat()}, "expires_on"),
        (
            {
                "start_date": (TODAY + timedelta(days=10)).isoformat(),
                "expires_on": (TODAY + timedelta(days=5)).isoformat(),
            },
            "expires_on",
        ),
    ],
)
def test_create_validates_input(world, overrides, field):
    response = create(world, **overrides)

    assert_error(response, 422, "validation_error")
    assert field in response.get_json()["error"]["fields"]


def test_inactive_template_cannot_be_used(world):
    world["admin"].delete(f"/api/quotation-templates/{world['template_id']}")

    assert_error(create(world), 422, "validation_error")


@pytest.mark.parametrize(
    "values",
    [
        {"is_active": False},
        {"valid_from": TODAY + timedelta(days=1)},
        {"valid_to": TODAY - timedelta(days=1), "valid_from": TODAY - timedelta(days=9)},
    ],
)
def test_unavailable_plan_cannot_be_sold(app, world, values):
    update_plan(app, world, **values)

    assert_error(create(world), 409, "plan_unavailable")


def test_template_with_a_retired_product_cannot_be_sold(app, world):
    with app.app_context():
        db.session.get(Product, world["catalog"]["product_id"]).is_active = False
        db.session.commit()

    assert_error(create(world), 409, "catalog_item_inactive")


def test_template_below_a_raised_plan_minimum_cannot_be_sold(app, world):
    update_plan(app, world, min_quantity=5)

    assert_error(create(world), 409, "below_plan_minimum")


# The state machine


def test_the_happy_path_from_draft_to_closed(world):
    subscription_id = create_id(world)

    statuses = [
        act(world, subscription_id, action).get_json()["status"]
        for action in ("send-quotation", "confirm", "activate", "close")
    ]

    assert statuses == ["quotation", "confirmed", "active", "closed"]


# Every move the spec allows. Any other combination must return 409.
ALLOWED_MOVES = {
    ("draft", "send-quotation"),
    ("quotation", "confirm"),
    ("confirmed", "activate"),
    ("active", "pause"),
    ("active", "renew"),
    ("active", "close"),
    ("paused", "resume"),
    ("paused", "close"),
}
ALL_STATUSES = ("draft", "quotation", "confirmed", "active", "paused", "closed")
ALL_ACTIONS = ("send-quotation", "confirm", "activate", "pause", "resume", "renew", "close")


def test_every_move_outside_the_table_returns_409_and_changes_nothing(app, world):
    # One test, not 34: creating the schema per test would be needlessly slow.
    subscription_id = create_id(world)
    unexpected = []

    for status in ALL_STATUSES:
        for action in ALL_ACTIONS:
            if (status, action) in ALLOWED_MOVES:
                continue
            update_subscription(
                app, subscription_id, status=status, next_billing_date=TODAY
            )
            response = act(world, subscription_id, action)
            with app.app_context():
                status_after = db.session.get(Subscription, subscription_id).status
            body = response.get_json()
            if (
                response.status_code != 409
                or body["error"]["code"] != "invalid_transition"
                or status_after != status
            ):
                unexpected.append((status, action, response.status_code, status_after))

    assert unexpected == []


def test_refused_move_writes_no_audit_entry(app, world):
    subscription_id = create_id(world)

    assert_error(act(world, subscription_id, "close"), 409, "invalid_transition")

    with app.app_context():
        actions = db.session.scalars(db.select(AuditLog.action)).all()
    assert "subscription.close" not in actions


def test_customers_cannot_move_a_subscription(world):
    subscription_id = create_id(world)

    response = world["customer"].post(f"{URL}/{subscription_id}/send-quotation")

    assert_error(response, 403, "forbidden")


def test_csrf_header_is_required_to_move_a_subscription(world):
    subscription_id = create_id(world)

    response = world["admin"].client.post(f"{URL}/{subscription_id}/send-quotation")

    assert_error(response, 401, "unauthorized")


def test_unknown_action_and_unknown_subscription_return_404(world):
    subscription_id = create_id(world)

    assert_error(act(world, subscription_id, "explode"), 404, "not_found")
    assert_error(act(world, 99999, "confirm"), 404, "not_found")


def test_a_successful_move_is_audited_with_both_statuses(app, world):
    subscription_id = create_id(world)

    act(world, subscription_id, "send-quotation")

    with app.app_context():
        entry = db.session.scalar(
            db.select(AuditLog).where(AuditLog.action == "subscription.send-quotation")
        )
        assert entry.entity_id == subscription_id
        assert entry.details == {"from": "draft", "to": "quotation"}


# Quotation validity


def test_sending_restarts_the_validity_period(app, world):
    subscription_id = create_id(world)
    update_subscription(app, subscription_id, quotation_valid_until=TODAY - timedelta(days=5))

    body = act(world, subscription_id, "send-quotation").get_json()

    assert body["quotation_valid_until"] == (TODAY + timedelta(days=30)).isoformat()


def test_expired_quotation_cannot_be_confirmed(app, world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, "send-quotation")
    update_subscription(app, subscription_id, quotation_valid_until=TODAY - timedelta(days=1))

    assert_error(act(world, subscription_id, "confirm"), 409, "quotation_expired")

    assert world["admin"].get(f"{URL}/{subscription_id}").get_json()["status"] == "quotation"


def test_quotation_can_be_confirmed_on_its_last_day(app, world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, "send-quotation")
    update_subscription(app, subscription_id, quotation_valid_until=TODAY)

    assert act(world, subscription_id, "confirm").status_code == 200


# Activation


def test_activating_starts_billing_today_by_default(world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, "send-quotation", "confirm")

    body = act(world, subscription_id, "activate").get_json()

    assert body["start_date"] == TODAY.isoformat()
    assert body["next_billing_date"] == TODAY.isoformat()


def test_activating_uses_a_chosen_start_date(world):
    start = TODAY + timedelta(days=7)
    subscription_id = create_id(world, start_date=start.isoformat())
    move_to(world, subscription_id, "send-quotation", "confirm")

    body = act(world, subscription_id, "activate").get_json()

    assert body["next_billing_date"] == start.isoformat()


def test_cannot_activate_after_the_expiry_date(app, world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, "send-quotation", "confirm")
    update_subscription(app, subscription_id, expires_on=TODAY - timedelta(days=1))

    assert_error(act(world, subscription_id, "activate"), 409, "subscription_expired")


# Plan flags


@pytest.mark.parametrize(
    "flag, action",
    [("is_pausable", "pause"), ("is_renewable", "renew"), ("is_closable", "close")],
)
def test_plan_flags_can_forbid_a_move(app, world, flag, action):
    subscription_id = create_id(world, expires_on=(TODAY + timedelta(days=60)).isoformat())
    move_to(world, subscription_id, *TO_ACTIVE)
    update_plan(app, world, **{flag: False})

    assert_error(act(world, subscription_id, action), 409, "action_not_allowed_by_plan")

    assert world["admin"].get(f"{URL}/{subscription_id}").get_json()["status"] == "active"


def test_flag_applies_when_closing_a_paused_subscription(app, world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, *TO_ACTIVE, "pause")
    update_plan(app, world, is_closable=False)

    assert_error(act(world, subscription_id, "close"), 409, "action_not_allowed_by_plan")


# Pause, resume, renew, close


def test_pause_then_resume_keeps_a_future_billing_date(app, world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, *TO_ACTIVE)
    future = TODAY + timedelta(days=10)
    update_subscription(app, subscription_id, next_billing_date=future)

    move_to(world, subscription_id, "pause")
    body = act(world, subscription_id, "resume").get_json()

    assert body["status"] == "active"
    assert body["next_billing_date"] == future.isoformat()


def test_resuming_does_not_bill_the_time_spent_paused(app, world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, *TO_ACTIVE, "pause")
    old_date = TODAY - timedelta(days=75)
    update_subscription(app, subscription_id, next_billing_date=old_date)

    body = act(world, subscription_id, "resume").get_json()

    new_date = date.fromisoformat(body["next_billing_date"])
    assert TODAY <= new_date
    assert new_date < add_billing_period(TODAY, "monthly")


def test_renew_extends_the_expiry_by_one_billing_period(world):
    expiry = TODAY + timedelta(days=20)
    subscription_id = create_id(world, expires_on=expiry.isoformat())
    move_to(world, subscription_id, *TO_ACTIVE)

    body = act(world, subscription_id, "renew").get_json()

    assert body["status"] == "active"
    assert body["expires_on"] == add_billing_period(expiry, "monthly").isoformat()


def test_renewing_without_an_expiry_date_is_refused(world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, *TO_ACTIVE)

    assert_error(act(world, subscription_id, "renew"), 409, "no_expiry_date")


def test_closing_records_when(world):
    subscription_id = create_id(world)
    move_to(world, subscription_id, *TO_ACTIVE)

    assert act(world, subscription_id, "close").get_json()["closed_at"] is not None


# Customer scoping


def test_customer_sees_only_their_own_subscriptions(app, world):
    own_id = create_id(world)
    other_client, other_customer_id = make_customer(app, "other@example.com", "Other")
    other_id = create_id(world, customer_id=other_customer_id)

    listed = world["customer"].get(URL).get_json()

    assert [item["id"] for item in listed["items"]] == [own_id]
    assert listed["total"] == 1
    assert world["customer"].get(f"{URL}/{own_id}").status_code == 200
    assert other_client.get(f"{URL}/{other_id}").status_code == 200


def test_another_customers_subscription_looks_like_it_does_not_exist(app, world):
    other_client, _ = make_customer(app, "other@example.com", "Other")
    subscription_id = create_id(world)

    response = other_client.get(f"{URL}/{subscription_id}")
    missing = other_client.get(f"{URL}/99999")

    assert_error(response, 404, "not_found")
    assert response.get_json() == missing.get_json()


def test_customer_login_without_a_customer_record_sees_nothing(app, world):
    create_id(world)
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email == "customer@example.com"))
        customer = db.session.scalar(db.select(Customer).where(Customer.user_id == user.id))
        customer.user_id = None
        db.session.commit()

    assert_error(world["customer"].get(URL), 403, "forbidden")
    assert_error(world["customer"].get(f"{URL}/1"), 403, "forbidden")


def test_staff_see_every_customer(app, world):
    create_id(world)
    _, other_customer_id = make_customer(app, "other@example.com", "Other")
    create_id(world, customer_id=other_customer_id)
    staff = make_staff(app)

    assert staff.get(URL).get_json()["total"] == 2


def test_list_filters_by_status_and_paginates(world):
    active_id = create_id(world)
    move_to(world, active_id, *TO_ACTIVE)
    create_id(world)
    admin = world["admin"]

    assert [i["id"] for i in admin.get(URL, query_string={"status": "active"}).get_json()["items"]] == [active_id]
    assert admin.get(URL, query_string={"status": "draft"}).get_json()["total"] == 1
    assert_error(admin.get(URL, query_string={"status": "bogus"}), 422, "validation_error")
    page = admin.get(URL, query_string={"per_page": 1}).get_json()
    assert len(page["items"]) == 1
    assert page["total"] == 2


def test_login_is_required_to_read(app):
    assert_error(ApiClient(app).get(URL), 401, "unauthorized")


# Date arithmetic


@pytest.mark.parametrize(
    "start, period, interval, expected",
    [
        (date(2026, 1, 15), "daily", 1, date(2026, 1, 16)),
        (date(2026, 1, 15), "weekly", 2, date(2026, 1, 29)),
        (date(2026, 1, 15), "monthly", 1, date(2026, 2, 15)),
        (date(2026, 1, 31), "monthly", 1, date(2026, 2, 28)),
        (date(2028, 1, 31), "monthly", 1, date(2028, 2, 29)),
        (date(2026, 11, 30), "monthly", 3, date(2027, 2, 28)),
        (date(2026, 12, 15), "monthly", 1, date(2027, 1, 15)),
        (date(2028, 2, 29), "yearly", 1, date(2029, 2, 28)),
    ],
)
def test_add_billing_period(start, period, interval, expected):
    assert add_billing_period(start, period, interval) == expected
