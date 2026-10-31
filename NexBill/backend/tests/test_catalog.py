"""Catalog: taxes, products with variants, plans and discounts."""
import pytest

from helpers import ApiClient, assert_error, make_admin, make_customer, make_staff

TAX = {"name": "GST 18%", "rate": "18.00"}
PRODUCT = {
    "name": "Hosting",
    "sales_price": "1000.00",
    "variants": [{"attribute": "Brand", "value": "Odoo", "extra_price": "560.00"}],
}
PLAN = {"name": "Monthly", "billing_period": "monthly", "is_pausable": True}
DISCOUNT = {
    "code": "SAVE10",
    "name": "Save 10",
    "discount_type": "percent",
    "value": "10.00",
    "usage_limit": 5,
}
RESOURCES = [
    ("/api/taxes", TAX),
    ("/api/products", PRODUCT),
    ("/api/plans", PLAN),
    ("/api/discounts", DISCOUNT),
]


def test_admin_creates_a_tax_with_money_as_a_string(app):
    response = make_admin(app).post("/api/taxes", TAX)

    assert response.status_code == 201
    body = response.get_json()
    assert body["rate"] == "18.00"
    assert body["is_active"] is True


def test_admin_creates_a_product_with_its_variant(app):
    body = make_admin(app).post("/api/products", PRODUCT).get_json()

    assert body["sales_price"] == "1000.00"
    assert body["product_type"] == "service"
    [variant] = body["variants"]
    assert (variant["attribute"], variant["value"], variant["extra_price"]) == ("Brand", "Odoo", "560.00")


def test_admin_creates_a_plan_with_its_flags(app):
    body = make_admin(app).post("/api/plans", PLAN).get_json()

    assert body["billing_period"] == "monthly"
    assert body["is_pausable"] is True
    assert body["is_renewable"] is False


def test_admin_creates_a_discount_with_a_usage_limit(app):
    body = make_admin(app).post("/api/discounts", DISCOUNT).get_json()

    assert body["usage_limit"] == 5
    assert body["usage_count"] == 0
    assert body["scope"] == "subscription"


@pytest.mark.parametrize("url, payload", RESOURCES)
def test_only_admins_can_create(app, url, payload):
    staff = make_staff(app)
    customer, _ = make_customer(app)

    assert_error(staff.post(url, payload), 403, "forbidden")
    assert_error(customer.post(url, payload), 403, "forbidden")
    assert_error(ApiClient(app).post(url, payload), 401, "unauthorized")


@pytest.mark.parametrize("url, payload", RESOURCES)
def test_staff_can_list_but_customers_cannot(app, url, payload):
    make_admin(app).post(url, payload)
    customer, _ = make_customer(app)

    body = make_staff(app).get(url, query_string={"page_size": 100}).get_json()

    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 100
    assert len(body["items"]) == 1
    assert_error(customer.get(url), 403, "forbidden")


@pytest.mark.parametrize("url, payload", RESOURCES)
def test_page_size_above_100_is_refused(app, url, payload):
    assert_error(make_admin(app).get(url, query_string={"page_size": 101}), 422, "validation_error")


@pytest.mark.parametrize(
    "url, payload, field",
    [
        ("/api/taxes", TAX, "name"),
        ("/api/products", PRODUCT, "name"),
        ("/api/plans", PLAN, "name"),
        ("/api/discounts", DISCOUNT, "code"),
    ],
)
def test_duplicate_is_a_conflict_on_the_right_field(app, url, payload, field):
    admin = make_admin(app)
    admin.post(url, payload)

    response = admin.post(url, payload)

    assert_error(response, 409, "name_taken")
    assert field in response.get_json()["error"]["fields"]


@pytest.mark.parametrize(
    "url, payload, field",
    [
        ("/api/taxes", {**TAX, "rate": "100.01"}, "rate"),
        ("/api/taxes", {**TAX, "rate": "-1"}, "rate"),
        ("/api/products", {**PRODUCT, "sales_price": "-1"}, "sales_price"),
        ("/api/products", {**PRODUCT, "sales_price": "1.234"}, "sales_price"),
        ("/api/products", {**PRODUCT, "variants": PRODUCT["variants"] * 2}, "variants"),
        ("/api/plans", {**PLAN, "billing_period": "hourly"}, "billing_period"),
        ("/api/plans", {**PLAN, "billing_interval": 0}, "billing_interval"),
        ("/api/plans", {**PLAN, "valid_from": "2026-02-01", "valid_to": "2026-01-01"}, "valid_to"),
        ("/api/discounts", {**DISCOUNT, "value": "100.01"}, "value"),
        ("/api/discounts", {**DISCOUNT, "value": "0"}, "value"),
        ("/api/discounts", {**DISCOUNT, "usage_limit": -1}, "usage_limit"),
        ("/api/discounts", {**DISCOUNT, "scope": "product"}, "product_ids"),
        ("/api/discounts", {**DISCOUNT, "product_ids": [1]}, "product_ids"),
    ],
)
def test_bad_input_returns_422_naming_the_field(app, url, payload, field):
    response = make_admin(app).post(url, payload)

    assert_error(response, 422, "validation_error")
    assert field in response.get_json()["error"]["fields"]


def test_product_discount_lists_its_products(app):
    admin = make_admin(app)
    product_id = admin.post("/api/products", PRODUCT).get_json()["id"]

    body = admin.post(
        "/api/discounts", {**DISCOUNT, "scope": "product", "product_ids": [product_id]}
    ).get_json()

    assert body["product_ids"] == [product_id]


def test_product_discount_refuses_an_unknown_product(app):
    response = make_admin(app).post(
        "/api/discounts", {**DISCOUNT, "scope": "product", "product_ids": [99999]}
    )

    assert_error(response, 422, "validation_error")


def test_new_items_can_be_used_in_a_template(app):
    admin = make_admin(app)
    tax_id = admin.post("/api/taxes", TAX).get_json()["id"]
    product = admin.post("/api/products", PRODUCT).get_json()
    plan_id = admin.post("/api/plans", PLAN).get_json()["id"]

    response = admin.post(
        "/api/quotation-templates",
        {
            "name": "Standard",
            "plan_id": plan_id,
            "validity_days": 30,
            "lines": [
                {
                    "product_id": product["id"],
                    "variant_id": product["variants"][0]["id"],
                    "tax_id": tax_id,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201
