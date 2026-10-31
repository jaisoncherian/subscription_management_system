"""Invoice states, payments, overdue, and customer scoping."""
import threading
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import AuditLog, Invoice, InvoiceLine, Payment, Subscription, User
from app.services import mail_service, payment_service
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

URL = "/api/invoices"
TODAY = date.today()


@pytest.fixture
def world(app):
    admin = make_admin(app)
    catalog = make_catalog(app)
    template_id = admin.post(
        "/api/quotation-templates", template_payload(catalog)
    ).get_json()["id"]
    customer, customer_id = make_customer(app)
    other, other_customer_id = make_customer(app, "other@example.com", "Other")
    subscription_id = make_active_subscription(app, admin, customer_id, template_id)
    other_subscription_id = make_active_subscription(app, admin, other_customer_id, template_id)
    return {
        "app": app,
        "admin": admin,
        "customer": customer,
        "customer_id": customer_id,
        "other": other,
        "other_customer_id": other_customer_id,
        "subscription_id": subscription_id,
        "other_subscription_id": other_subscription_id,
    }


COUNTER = iter(range(1, 100000))


def make_invoice(world, status="confirmed", total="1000.00", other=False, **overrides):
    """Written directly, so that these tests do not depend on the billing run."""
    number = next(COUNTER)
    values = {
        "invoice_number": f"INV-T{number}",
        "subscription_id": world["other_subscription_id" if other else "subscription_id"],
        "customer_id": world["other_customer_id" if other else "customer_id"],
        "customer_snapshot": {"name": "<b>Customer</b>", "email": "customer@example.com"},
        "status": status,
        "period_start": TODAY - timedelta(days=number),
        "period_end": TODAY - timedelta(days=number),
        "invoice_date": TODAY,
        "due_date": TODAY + timedelta(days=15),
        "subtotal": Decimal(total),
        "total": Decimal(total),
    }
    values.update(overrides)
    with world["app"].app_context():
        invoice = Invoice(**values)
        invoice.lines = [
            InvoiceLine(
                description="Hosting <i>Pro</i>",
                quantity=1,
                unit_price=Decimal(total),
                line_total=Decimal(total),
            )
        ]
        db.session.add(invoice)
        db.session.commit()
        return invoice.id


def act(world, invoice_id, action):
    return world["admin"].post(f"{URL}/{invoice_id}/{action}")


def pay(world, invoice_id, amount="1000.00", **extra):
    return world["admin"].post(
        f"{URL}/{invoice_id}/payments", {"method": "card", "amount": amount, **extra}
    )


def status_of(world, invoice_id):
    return world["admin"].get(f"{URL}/{invoice_id}").get_json()["status"]


# State machine


def test_draft_confirm_pay_reaches_paid(world):
    invoice_id = make_invoice(world, status="draft")

    confirmed = act(world, invoice_id, "confirm").get_json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["confirmed_at"] is not None

    assert pay(world, invoice_id).status_code == 201
    assert status_of(world, invoice_id) == "paid"


@pytest.mark.parametrize(
    "status, action",
    [
        ("confirmed", "confirm"),
        ("paid", "confirm"),
        ("cancelled", "confirm"),
        ("paid", "cancel"),
        ("cancelled", "cancel"),
    ],
)
def test_invalid_moves_return_409_and_change_nothing(world, status, action):
    invoice_id = make_invoice(world, status=status)

    assert_error(act(world, invoice_id, action), 409, "invalid_transition")

    assert status_of(world, invoice_id) == status


@pytest.mark.parametrize("status", ["draft", "confirmed"])
def test_can_cancel_before_paid(world, status):
    invoice_id = make_invoice(world, status=status)

    body = act(world, invoice_id, "cancel").get_json()

    assert body["status"] == "cancelled"
    assert body["cancelled_at"] is not None


def test_cannot_cancel_once_partly_paid(world):
    invoice_id = make_invoice(world)
    pay(world, invoice_id, "100.00")

    assert_error(act(world, invoice_id, "cancel"), 409, "invoice_has_payments")

    assert status_of(world, invoice_id) == "confirmed"


def test_zero_total_invoice_settles_on_confirm(world):
    invoice_id = make_invoice(world, status="draft", total="0.00")

    body = act(world, invoice_id, "confirm").get_json()

    assert body["status"] == "paid"
    assert body["paid_at"] is not None


def test_unknown_invoice_and_action_return_404(world):
    assert_error(act(world, 99999, "confirm"), 404, "not_found")
    assert_error(act(world, make_invoice(world), "explode"), 404, "not_found")


# Payments


def test_full_payment_flips_invoice_to_paid(world):
    invoice_id = make_invoice(world)

    response = pay(world, invoice_id, note="Paid by card", payment_date=TODAY.isoformat())

    assert response.status_code == 201
    body = response.get_json()
    assert body["amount"] == "1000.00"
    assert body["method"] == "card"
    assert body["note"] == "Paid by card"
    invoice = world["admin"].get(f"{URL}/{invoice_id}").get_json()
    assert invoice["status"] == "paid"
    assert invoice["amount_paid"] == "1000.00"
    assert invoice["balance_due"] == "0.00"
    assert invoice["paid_at"] is not None


def test_partial_payments_flip_to_paid_only_at_the_end(world):
    invoice_id = make_invoice(world)

    pay(world, invoice_id, "400.00")
    assert status_of(world, invoice_id) == "confirmed"
    assert world["admin"].get(f"{URL}/{invoice_id}").get_json()["balance_due"] == "600.00"

    pay(world, invoice_id, "600.00")
    assert status_of(world, invoice_id) == "paid"
    assert len(world["admin"].get(f"{URL}/{invoice_id}/payments").get_json()) == 2


def test_overpayment_is_rejected_and_records_nothing(app, world):
    invoice_id = make_invoice(world)
    pay(world, invoice_id, "900.00")

    response = pay(world, invoice_id, "100.01")

    assert_error(response, 409, "overpayment")
    assert "amount" in response.get_json()["error"]["fields"]
    with app.app_context():
        assert len(db.session.scalars(db.select(Payment)).all()) == 1
    assert world["admin"].get(f"{URL}/{invoice_id}").get_json()["amount_paid"] == "900.00"


@pytest.mark.parametrize("status", ["draft", "paid", "cancelled"])
def test_only_confirmed_invoices_take_payments(world, status):
    invoice_id = make_invoice(world, status=status)

    assert_error(pay(world, invoice_id, "1.00"), 409, "invoice_not_payable")


@pytest.mark.parametrize(
    "payload, field",
    [
        ({"method": "card", "amount": "0"}, "amount"),
        ({"method": "card", "amount": "-5.00"}, "amount"),
        ({"method": "card", "amount": "1.005"}, "amount"),
        ({"method": "card", "amount": "NaN"}, "amount"),
        ({"method": "card"}, "amount"),
        ({"method": "bitcoin", "amount": "1.00"}, "method"),
        ({"amount": "1.00"}, "method"),
        ({"method": "card", "amount": "1.00", "payment_date": "nope"}, "payment_date"),
    ],
)
def test_payment_input_is_validated(world, payload, field):
    invoice_id = make_invoice(world)

    response = world["admin"].post(f"{URL}/{invoice_id}/payments", payload)

    assert_error(response, 422, "validation_error")
    assert field in response.get_json()["error"]["fields"]


def test_future_payment_date_is_rejected(world):
    invoice_id = make_invoice(world)
    tomorrow = (TODAY + timedelta(days=1)).isoformat()

    assert_error(pay(world, invoice_id, payment_date=tomorrow), 422, "validation_error")


def test_payment_date_defaults_to_today(world):
    invoice_id = make_invoice(world)

    assert pay(world, invoice_id).get_json()["payment_date"] == TODAY.isoformat()


def test_payment_is_audited_with_who_recorded_it(app, world):
    invoice_id = make_invoice(world)
    pay(world, invoice_id, "250.00")

    with app.app_context():
        entry = db.session.scalar(
            db.select(AuditLog).where(AuditLog.action == "payment.recorded")
        )
        payment = db.session.scalar(db.select(Payment))
        assert entry.details["amount"] == "250.00"
        assert entry.actor_user_id == payment.recorded_by_user_id is not None


@pytest.mark.postgres
def test_simultaneous_payments_cannot_overpay(app, world):
    invoice_id = make_invoice(world, total="1000.00")
    with app.app_context():
        admin_id = db.session.scalar(db.select(User.id).where(User.role == "admin"))
    outcomes = []
    barrier = threading.Barrier(5)

    def worker():
        with app.app_context():
            actor = db.session.get(User, admin_id)
            barrier.wait()
            try:
                payment_service.record_payment(actor, invoice_id, "card", Decimal("400.00"))
                outcomes.append("paid")
            except Exception as error:
                outcomes.append(getattr(error, "code", repr(error)))
                db.session.rollback()

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["overpayment"] * 3 + ["paid"] * 2
    body = world["admin"].get(f"{URL}/{invoice_id}").get_json()
    assert body["amount_paid"] == "800.00"
    assert body["status"] == "confirmed"


# Overdue is computed


def test_overdue_is_computed_from_status_and_due_date(world):
    past = {
        "invoice_date": TODAY - timedelta(days=30),
        "due_date": TODAY - timedelta(days=1),
    }
    overdue = make_invoice(world, **past)
    due_today = make_invoice(world, due_date=TODAY)
    draft_past_due = make_invoice(world, status="draft", **past)
    paid_past_due = make_invoice(world, status="paid", **past)
    get = lambda i: world["admin"].get(f"{URL}/{i}").get_json()["is_overdue"]  # noqa: E731

    assert get(overdue) is True
    assert get(due_today) is False
    assert get(draft_past_due) is False
    assert get(paid_past_due) is False


def test_invoice_model_stores_no_overdue_flag():
    assert not any("overdue" in column.name for column in Invoice.__table__.columns)


def test_list_can_filter_to_overdue_invoices(world):
    overdue = make_invoice(
        world, invoice_date=TODAY - timedelta(days=30), due_date=TODAY - timedelta(days=1)
    )
    make_invoice(world)

    body = world["admin"].get(URL, query_string={"overdue": "true"}).get_json()

    assert [item["id"] for item in body["items"]] == [overdue]
    assert body["total"] == 1
    assert body["items"][0]["is_overdue"] is True


def test_partly_paid_invoice_can_still_be_overdue(world):
    invoice_id = make_invoice(
        world, invoice_date=TODAY - timedelta(days=30), due_date=TODAY - timedelta(days=1)
    )
    pay(world, invoice_id, "100.00")

    assert world["admin"].get(f"{URL}/{invoice_id}").get_json()["is_overdue"] is True


def test_list_filters_and_paginates(world):
    first = make_invoice(world, status="draft")
    make_invoice(world)
    make_invoice(world, other=True)
    admin = world["admin"]

    assert admin.get(URL).get_json()["total"] == 3
    drafts = admin.get(URL, query_string={"status": "draft"}).get_json()
    assert [item["id"] for item in drafts["items"]] == [first]
    by_customer = admin.get(
        URL, query_string={"customer_id": world["other_customer_id"]}
    ).get_json()
    assert by_customer["total"] == 1
    page = admin.get(URL, query_string={"page_size": 2, "page": 2}).get_json()
    assert len(page["items"]) == 1
    assert page["total"] == 3
    assert_error(admin.get(URL, query_string={"status": "bogus"}), 422, "validation_error")


# Customer scoping


def test_customer_cannot_read_another_customers_invoice(world):
    theirs = make_invoice(world, other=True)
    missing_response = world["customer"].get(f"{URL}/99999")

    response = world["customer"].get(f"{URL}/{theirs}")

    assert_error(response, 404, "not_found")
    assert response.get_json() == missing_response.get_json()
    assert_error(world["customer"].get(f"{URL}/{theirs}/print"), 404, "not_found")
    assert_error(world["customer"].get(f"{URL}/{theirs}/payments"), 404, "not_found")


def test_customer_list_shows_only_their_own_issued_invoices(world):
    own = make_invoice(world)
    make_invoice(world, status="draft")
    make_invoice(world, other=True)

    body = world["customer"].get(URL).get_json()

    assert [item["id"] for item in body["items"]] == [own]
    assert body["total"] == 1


def test_customer_cannot_widen_the_list_with_a_filter(world):
    make_invoice(world, other=True)

    body = world["customer"].get(
        URL, query_string={"customer_id": world["other_customer_id"]}
    ).get_json()

    assert body["items"] == []
    assert body["total"] == 0


def test_customer_cannot_see_their_own_draft(world):
    draft = make_invoice(world, status="draft")

    assert_error(world["customer"].get(f"{URL}/{draft}"), 404, "not_found")


def test_customer_can_read_their_invoice_and_its_payments(world):
    own = make_invoice(world)
    pay(world, own, "100.00")

    assert world["customer"].get(f"{URL}/{own}").status_code == 200
    assert len(world["customer"].get(f"{URL}/{own}/payments").get_json()) == 1
    assert world["customer"].get(f"{URL}/{own}/print").status_code == 200


def test_customer_cannot_change_invoices(world):
    own = make_invoice(world)
    customer = world["customer"]

    assert_error(customer.post(f"{URL}/{own}/confirm"), 403, "forbidden")
    assert_error(customer.post(f"{URL}/{own}/cancel"), 403, "forbidden")
    assert_error(customer.post(f"{URL}/{own}/send"), 403, "forbidden")
    assert_error(
        customer.post(f"{URL}/{own}/payments", {"method": "card", "amount": "1.00"}),
        403,
        "forbidden",
    )


def test_login_and_csrf_are_required(app, world):
    invoice_id = make_invoice(world)

    assert_error(ApiClient(app).get(URL), 401, "unauthorized")
    assert_error(ApiClient(app).get(f"{URL}/{invoice_id}/print"), 401, "unauthorized")
    response = world["admin"].client.post(
        f"{URL}/{invoice_id}/payments", json={"method": "card", "amount": "1.00"}
    )
    assert_error(response, 401, "unauthorized")


def test_staff_can_manage_invoices(app, world):
    staff = make_staff(app)
    invoice_id = make_invoice(world, status="draft")

    assert staff.post(f"{URL}/{invoice_id}/confirm").status_code == 200
    assert (
        staff.post(
            f"{URL}/{invoice_id}/payments", {"method": "cash", "amount": "1000.00"}
        ).status_code
        == 201
    )


# Send and print


@pytest.fixture
def sent_emails(monkeypatch):
    emails = []
    monkeypatch.setattr(
        mail_service,
        "send_email",
        lambda to, subject, body: emails.append({"to": to, "subject": subject, "body": body}),
    )
    return emails


def test_send_emails_the_customer_and_records_when(world, sent_emails):
    invoice_id = make_invoice(world)

    body = act(world, invoice_id, "send").get_json()

    assert body["sent_at"] is not None
    assert sent_emails[0]["to"] == "customer@example.com"
    assert body["invoice_number"] in sent_emails[0]["subject"]
    assert "1000.00" in sent_emails[0]["body"]


@pytest.mark.parametrize("status", ["draft", "cancelled"])
def test_unissued_invoices_cannot_be_sent(world, sent_emails, status):
    invoice_id = make_invoice(world, status=status)

    assert_error(act(world, invoice_id, "send"), 409, "invoice_not_sendable")

    assert sent_emails == []


def test_print_returns_html_with_the_invoice(world):
    invoice_id = make_invoice(world)

    response = world["admin"].get(f"{URL}/{invoice_id}/print")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    text = response.get_data(as_text=True)
    assert "Invoice INV-T" in text
    assert "1000.00" in text


def test_print_escapes_customer_supplied_text(world):
    invoice_id = make_invoice(world)

    text = world["admin"].get(f"{URL}/{invoice_id}/print").get_data(as_text=True)

    assert "<b>Customer</b>" not in text
    assert "&lt;b&gt;Customer&lt;/b&gt;" in text
    assert "<i>Pro</i>" not in text


def test_print_marks_an_overdue_invoice(world):
    invoice_id = make_invoice(
        world, invoice_date=TODAY - timedelta(days=30), due_date=TODAY - timedelta(days=1)
    )

    assert "Overdue" in world["admin"].get(f"{URL}/{invoice_id}/print").get_data(as_text=True)


def test_invoice_response_snapshot_survives_a_subscription_change(app, world):
    invoice_id = make_invoice(world)
    with app.app_context():
        subscription = db.session.get(Subscription, world["subscription_id"])
        subscription.notes = "changed"
        db.session.commit()

    body = world["admin"].get(f"{URL}/{invoice_id}").get_json()

    assert body["customer_snapshot"]["name"] == "<b>Customer</b>"
