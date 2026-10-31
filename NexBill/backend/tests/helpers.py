"""Shared test helpers: logins that send the CSRF header, and catalog data."""
from decimal import Decimal

from app.extensions import db
from app.models import Plan, Product, ProductVariant, Tax
from app.models.enums import BillingPeriod
from app.models.user import Customer
from app.services import user_service

PASSWORD = "Str0ng!Password"


class ApiClient:
    """A logged-in test client that adds the CSRF header to every write."""

    def __init__(self, app, email=None):
        self.client = app.test_client()
        if email:
            response = self.client.post(
                "/api/auth/login", json={"email": email, "password": PASSWORD}
            )
            assert response.status_code == 200, response.get_json()

    def _headers(self):
        cookie = self.client.get_cookie("csrf_access_token")
        return {"X-CSRF-TOKEN": cookie.value} if cookie else {}

    def get(self, url, **kwargs):
        return self.client.get(url, **kwargs)

    def post(self, url, json=None):
        return self.client.post(url, json=json, headers=self._headers())

    def put(self, url, json=None):
        return self.client.put(url, json=json, headers=self._headers())

    def delete(self, url):
        return self.client.delete(url, headers=self._headers())


def make_admin(app, email="admin@example.com"):
    with app.app_context():
        user_service.ensure_admin(email, PASSWORD)
    return ApiClient(app, email)


def make_staff(app, email="staff@example.com"):
    with app.app_context():
        user_service.create_staff(None, email, PASSWORD, "Staff", "sales_rep")
    return ApiClient(app, email)


def make_customer(app, email="customer@example.com", name="Customer"):
    """Returns the logged-in client and the customer's id."""
    response = app.test_client().post(
        "/api/auth/register", json={"email": email, "password": PASSWORD, "full_name": name}
    )
    assert response.status_code == 201, response.get_json()
    with app.app_context():
        customer_id = db.session.scalar(
            db.select(Customer.id).where(Customer.email == email)
        )
    return ApiClient(app, email), customer_id


def make_catalog(app, plan_overrides=None):
    """Returns a dict of ids: a plan, a product with an Odoo +560 variant, and a tax."""
    with app.app_context():
        plan = Plan(
            name="Monthly",
            price=Decimal("0.00"),
            billing_period=BillingPeriod.MONTHLY,
            **(plan_overrides or {}),
        )
        product = Product(name="Hosting", sales_price=Decimal("1000.00"))
        other_product = Product(name="Support", sales_price=Decimal("200.00"))
        tax = Tax(name="GST 18%", rate=Decimal("18.00"))
        db.session.add_all([plan, product, other_product, tax])
        db.session.flush()
        variant = ProductVariant(
            product_id=product.id,
            attribute="Brand",
            value="Odoo",
            extra_price=Decimal("560.00"),
        )
        db.session.add(variant)
        db.session.commit()
        return {
            "plan_id": plan.id,
            "product_id": product.id,
            "other_product_id": other_product.id,
            "variant_id": variant.id,
            "tax_id": tax.id,
        }


def template_payload(catalog, name="Standard", validity_days=30, **overrides):
    return {
        "name": name,
        "plan_id": catalog["plan_id"],
        "validity_days": validity_days,
        "lines": [
            {
                "product_id": catalog["product_id"],
                "variant_id": catalog["variant_id"],
                "tax_id": catalog["tax_id"],
                "quantity": 2,
            }
        ],
        **overrides,
    }


def make_active_subscription(
    app, admin, customer_id, template_id, start_date=None, expires_on=None, discount_id=None
):
    """Create a subscription and move it to active. Returns its id."""
    payload = {"customer_id": customer_id, "template_id": template_id}
    if start_date:
        payload["start_date"] = start_date.isoformat()
    if expires_on:
        payload["expires_on"] = expires_on.isoformat()
    if discount_id:
        payload["discount_id"] = discount_id
    response = admin.post("/api/subscriptions", payload)
    assert response.status_code == 201, response.get_json()
    subscription_id = response.get_json()["id"]
    for action in ("send-quotation", "confirm", "activate"):
        response = admin.post(f"/api/subscriptions/{subscription_id}/{action}")
        assert response.status_code == 200, response.get_json()
    return subscription_id


def assert_error(response, status, code):
    assert response.status_code == status, response.get_json()
    body = response.get_json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "fields"}
    assert body["error"]["code"] == code
