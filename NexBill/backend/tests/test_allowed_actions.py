"""allowed_actions tells the client which buttons to show."""
from datetime import date

from helpers import (
    make_active_subscription,
    make_admin,
    make_catalog,
    make_customer,
    template_payload,
)

SUBSCRIPTIONS = "/api/subscriptions"
INVOICES = "/api/invoices"


def _setup(app, plan_overrides=None):
    admin = make_admin(app)
    catalog = make_catalog(app, plan_overrides)
    template = admin.post("/api/quotation-templates", template_payload(catalog)).get_json()
    customer, customer_id = make_customer(app)
    return admin, customer, customer_id, template["id"]


def test_each_status_lists_only_its_moves(app):
    admin, _, customer_id, template_id = _setup(
        app, {"is_pausable": True, "is_renewable": True}
    )

    created = admin.post(
        SUBSCRIPTIONS,
        {"customer_id": customer_id, "template_id": template_id, "expires_on": "2099-01-01"},
    ).get_json()
    assert created["allowed_actions"] == ["send-quotation"]

    url = f"{SUBSCRIPTIONS}/{created['id']}"
    assert admin.post(f"{url}/send-quotation").get_json()["allowed_actions"] == ["confirm"]
    assert admin.post(f"{url}/confirm").get_json()["allowed_actions"] == ["activate"]
    active = admin.post(f"{url}/activate").get_json()
    assert set(active["allowed_actions"]) == {"pause", "renew", "close"}
    assert set(admin.post(f"{url}/pause").get_json()["allowed_actions"]) == {"resume", "close"}
    assert admin.post(f"{url}/close").get_json()["allowed_actions"] == []


def test_plan_flags_and_a_missing_expiry_remove_actions(app):
    admin, _, customer_id, template_id = _setup(app, {"is_renewable": True, "is_closable": False})

    subscription_id = make_active_subscription(app, admin, customer_id, template_id)

    # Not pausable or closable by plan, and renew needs an expiry date.
    body = admin.get(f"{SUBSCRIPTIONS}/{subscription_id}").get_json()
    assert body["allowed_actions"] == []


def test_every_listed_action_really_works(app):
    admin, _, customer_id, template_id = _setup(app, {"is_pausable": True})
    subscription_id = make_active_subscription(app, admin, customer_id, template_id)

    url = f"{SUBSCRIPTIONS}/{subscription_id}"
    actions = admin.get(url).get_json()["allowed_actions"]
    assert set(actions) == {"pause", "close"}
    assert admin.post(f"{url}/pause").status_code == 200


def test_customers_get_no_actions_on_their_own_subscription(app):
    admin, customer, customer_id, template_id = _setup(app)
    subscription_id = make_active_subscription(app, admin, customer_id, template_id)

    assert customer.get(f"{SUBSCRIPTIONS}/{subscription_id}").get_json()["allowed_actions"] == []


def test_invoice_actions_follow_its_status_and_payments(app):
    admin, customer, customer_id, template_id = _setup(app)
    make_active_subscription(
        app, admin, customer_id, template_id, start_date=date.today()
    )
    assert admin.post("/api/billing/run").get_json()["invoices_created"] == 1
    invoice_id = admin.get(INVOICES).get_json()["items"][0]["id"]
    url = f"{INVOICES}/{invoice_id}"

    assert admin.get(url).get_json()["allowed_actions"] == ["confirm", "cancel"]

    confirmed = admin.post(f"{url}/confirm").get_json()
    assert confirmed["allowed_actions"] == ["cancel", "send", "pay"]
    assert customer.get(url).get_json()["allowed_actions"] == []

    admin.post(f"{url}/payments", {"method": "card", "amount": "1.00"})
    part_paid = admin.get(url).get_json()
    assert part_paid["allowed_actions"] == ["send", "pay"]

    admin.post(f"{url}/payments", {"method": "card", "amount": part_paid["balance_due"]})
    paid = admin.get(url).get_json()
    assert paid["status"] == "paid"
    assert paid["allowed_actions"] == ["send"]


def test_print_page_allows_only_its_own_script(app):
    admin, _, customer_id, template_id = _setup(app)
    make_active_subscription(app, admin, customer_id, template_id, start_date=date.today())
    admin.post("/api/billing/run")
    invoice_id = admin.get(INVOICES).get_json()["items"][0]["id"]

    response = admin.get(f"{INVOICES}/{invoice_id}/print")

    policy = response.headers["Content-Security-Policy"]
    nonce = policy.split("'nonce-")[1].split("'")[0]
    page = response.get_data(as_text=True)
    assert f'<script nonce="{nonce}">' in page
    assert "onclick" not in page
    assert "unsafe-inline" not in policy.split("style-src")[0]


def test_list_items_leave_out_allowed_actions(app):
    admin, _, customer_id, template_id = _setup(app)
    make_active_subscription(app, admin, customer_id, template_id)

    item = admin.get(SUBSCRIPTIONS).get_json()["items"][0]

    assert "allowed_actions" not in item
