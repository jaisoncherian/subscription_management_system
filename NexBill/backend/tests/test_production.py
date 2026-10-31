"""Production safeguards, the single-server frontend, and new list endpoints."""
import pytest

from app import create_app
from app.config import ProductionConfig, TestingConfig
from helpers import assert_error, make_admin, make_customer, make_staff

GOOD_SECRET = "x" * 40


@pytest.fixture
def production_settings(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", GOOD_SECRET)
    monkeypatch.setattr(ProductionConfig, "JWT_SECRET_KEY", GOOD_SECRET)
    monkeypatch.setattr(
        ProductionConfig, "SQLALCHEMY_DATABASE_URI", "postgresql+psycopg://u:good@localhost/db"
    )
    monkeypatch.setattr(ProductionConfig, "FRONTEND_URL", "https://billing.example.com")
    monkeypatch.setattr(ProductionConfig, "JWT_COOKIE_SECURE", True)
    monkeypatch.setattr(ProductionConfig, "FRONTEND_DIST", None)
    return monkeypatch


def test_production_starts_with_good_settings(production_settings):
    app = create_app("production")

    assert app.config["JWT_COOKIE_SECURE"] is True


@pytest.mark.parametrize(
    "setting, value, expected",
    [
        ("SECRET_KEY", "short", "SECRET_KEY"),
        ("JWT_SECRET_KEY", "change-me-to-a-long-random-jwt-secret-key", "JWT_SECRET_KEY"),
        ("SQLALCHEMY_DATABASE_URI", "postgresql+psycopg://u:change-me@h/db", "DATABASE_URL"),
        ("SQLALCHEMY_DATABASE_URI", "sqlite:///x.db", "DATABASE_URL"),
        ("FRONTEND_URL", None, "FRONTEND_URL"),
    ],
)
def test_production_refuses_unsafe_settings(production_settings, setting, value, expected):
    production_settings.setattr(ProductionConfig, setting, value)

    with pytest.raises(RuntimeError, match=expected):
        create_app("production")


def test_every_response_has_security_headers(client):
    headers = client.get("/api/health").headers

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "script-src" not in headers["Content-Security-Policy"]
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert "Strict-Transport-Security" not in headers


def test_https_is_enforced_by_browsers_in_production(production_settings):
    headers = create_app("production").test_client().get("/api/health").headers

    assert "max-age" in headers["Strict-Transport-Security"]


def test_readiness_checks_the_database(client):
    assert client.get("/api/health/ready").get_json() == {"status": "ok"}


def test_oversized_request_is_refused(client):
    response = client.post(
        "/api/auth/login", data=b"x" * (1024 * 1024 + 1), content_type="application/json"
    )

    assert_error(response, 413, "request_entity_too_large")


@pytest.fixture
def built_frontend(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app shell</html>")
    (tmp_path / "assets" / "app-abc123.js").write_text("console.log(1)")
    (tmp_path.parent / "secret.txt").write_text("private")
    monkeypatch.setattr(TestingConfig, "FRONTEND_DIST", str(tmp_path))
    return create_app("testing").test_client()


def test_app_routes_get_the_react_shell(built_frontend):
    for path in ("/", "/login", "/portal/invoices/3"):
        with built_frontend.get(path) as response:
            assert response.status_code == 200
            assert b"app shell" in response.data
            assert response.headers["Cache-Control"] == "no-cache"


def test_hashed_assets_are_cached(built_frontend):
    with built_frontend.get("/assets/app-abc123.js") as response:
        assert response.status_code == 200
        assert "max-age=31536000" in response.headers["Cache-Control"]


def test_unknown_api_route_stays_a_json_404(built_frontend):
    assert_error(built_frontend.get("/api/nope"), 404, "not_found")


def test_missing_file_is_a_404_not_the_shell(built_frontend):
    assert built_frontend.get("/assets/missing.js").status_code == 404


def test_files_outside_dist_cannot_be_read(built_frontend):
    assert b"private" not in built_frontend.get("/../secret.txt").data
    assert b"private" not in built_frontend.get("/assets/..%2F..%2Fsecret.txt").data


def test_only_admins_list_staff(app):
    admin = make_admin(app)
    staff = make_staff(app)
    customer, _ = make_customer(app)

    body = admin.get("/api/staff").get_json()

    assert body["total"] == 1
    assert body["items"][0]["role"] == "staff"
    assert "password_hash" not in body["items"][0]
    assert_error(staff.get("/api/staff"), 403, "forbidden")
    assert_error(customer.get("/api/staff"), 403, "forbidden")


def test_customers_cannot_list_all_payments(app):
    customer, _ = make_customer(app)

    assert_error(customer.get("/api/payments"), 403, "forbidden")
    assert make_staff(app).get("/api/payments").get_json()["items"] == []


@pytest.mark.parametrize(
    "url, payload",
    [
        ("/api/taxes", {"name": "GST", "rate": "18.00"}),
        ("/api/products", {"name": "Hosting", "sales_price": "10.00"}),
        ("/api/plans", {"name": "Monthly", "billing_period": "monthly"}),
        ("/api/discounts", {"code": "A", "name": "A", "discount_type": "fixed", "value": "1.00"}),
    ],
)
def test_catalog_items_are_deactivated_not_deleted(app, url, payload):
    admin = make_admin(app)
    item_id = admin.post(url, payload).get_json()["id"]

    assert_error(make_staff(app).delete(f"{url}/{item_id}"), 403, "forbidden")
    response = admin.delete(f"{url}/{item_id}")

    assert response.status_code == 200
    assert response.get_json()["is_active"] is False
    assert admin.get(url).get_json()["items"][0]["is_active"] is False
    assert_error(admin.delete(f"{url}/99999"), 404, "not_found")
