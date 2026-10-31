"""flask seed-demo builds believable data through the real services."""
import pytest

from helpers import PASSWORD, ApiClient

ADMIN = "admin@example.com"


@pytest.fixture
def seeded(app):
    app.config.update(ADMIN_EMAIL=ADMIN, ADMIN_PASSWORD=PASSWORD, DEMO_PASSWORD=PASSWORD)
    result = app.test_cli_runner().invoke(args=["seed-demo"])
    assert result.exit_code == 0, result.output
    return result


def test_output_never_shows_a_password(seeded):
    assert PASSWORD not in seeded.output


@pytest.mark.postgres
def test_running_twice_changes_nothing(app, seeded):
    admin = ApiClient(app, ADMIN)
    before = admin.get("/api/invoices").get_json()["total"]

    second = app.test_cli_runner().invoke(args=["seed-demo"])

    assert second.exit_code == 0
    assert "Nothing changed" in second.output
    assert admin.get("/api/invoices").get_json()["total"] == before


@pytest.mark.postgres
def test_demo_data_fills_the_dashboard(app, seeded):
    admin = ApiClient(app, ADMIN)

    summary = admin.get("/api/reports/summary").get_json()
    months = admin.get("/api/reports/revenue?group=month").get_json()
    overdue = admin.get("/api/reports/overdue").get_json()

    assert summary["active_subscriptions"] >= 3
    assert float(summary["mrr"]) > 0
    assert float(summary["revenue_collected"]) > 0
    assert summary["overdue_count"] > 0
    assert overdue["total"] == summary["overdue_count"]
    assert len(months) >= 4
    statuses = {s["status"] for s in admin.get("/api/subscriptions?page_size=100").get_json()["items"]}
    assert statuses == {"draft", "quotation", "confirmed", "active", "paused", "closed"}


@pytest.mark.postgres
def test_seeded_logins_work_and_see_only_their_data(app, seeded):
    customer = ApiClient(app, "ana@acme.example")
    assert customer.get("/api/auth/me").get_json()["role"] == "customer"
    invoices = customer.get("/api/portal/invoices").get_json()
    assert invoices["total"] > 0
    assert all(item["status"] != "draft" for item in invoices["items"])
    assert ApiClient(app, "sales@brightloop.example").get("/api/customers").status_code == 200


def test_refuses_production(app):
    app.config.update(IS_PRODUCTION=True, ADMIN_EMAIL=ADMIN, ADMIN_PASSWORD=PASSWORD, DEMO_PASSWORD=PASSWORD)

    result = app.test_cli_runner().invoke(args=["seed-demo"])

    assert result.exit_code != 0
    assert "production" in result.output


def test_refuses_without_a_password(app):
    app.config.update(ADMIN_EMAIL=ADMIN, ADMIN_PASSWORD=PASSWORD, DEMO_PASSWORD=None)

    result = app.test_cli_runner().invoke(args=["seed-demo"])

    assert result.exit_code != 0
    assert "DEMO_PASSWORD" in result.output
