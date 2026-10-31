"""Quotation template management."""
from helpers import (
    ApiClient,
    assert_error,
    make_admin,
    make_catalog,
    make_customer,
    make_staff,
    template_payload,
)

URL = "/api/quotation-templates"


def test_admin_creates_a_template(app):
    admin = make_admin(app)
    catalog = make_catalog(app)

    response = admin.post(URL, template_payload(catalog))

    assert response.status_code == 201
    body = response.get_json()
    assert body["plan_name"] == "Monthly"
    assert body["validity_days"] == 30
    assert body["is_active"] is True
    assert [line["product_name"] for line in body["lines"]] == ["Hosting"]
    assert body["lines"][0]["quantity"] == 2


def test_only_admins_can_manage_templates(app):
    catalog = make_catalog(app)
    staff = make_staff(app)
    customer, _ = make_customer(app)

    assert_error(staff.post(URL, template_payload(catalog)), 403, "forbidden")
    assert_error(customer.post(URL, template_payload(catalog)), 403, "forbidden")
    assert_error(ApiClient(app).post(URL, template_payload(catalog)), 401, "unauthorized")


def test_staff_can_read_templates_but_customers_cannot(app):
    admin = make_admin(app)
    catalog = make_catalog(app)
    template_id = admin.post(URL, template_payload(catalog)).get_json()["id"]
    staff = make_staff(app)
    customer, _ = make_customer(app)

    assert staff.get(URL).get_json()["total"] == 1
    assert staff.get(f"{URL}/{template_id}").status_code == 200
    assert_error(customer.get(URL), 403, "forbidden")
    assert_error(customer.get(f"{URL}/{template_id}"), 403, "forbidden")


def test_variant_must_belong_to_the_product(app):
    admin = make_admin(app)
    catalog = make_catalog(app)
    payload = template_payload(catalog)
    payload["lines"][0]["product_id"] = catalog["other_product_id"]

    response = admin.post(URL, payload)

    assert_error(response, 422, "validation_error")
    assert "variant_id" in response.get_json()["error"]["fields"]["lines"]["0"]


def test_unknown_references_are_reported_per_field(app):
    admin = make_admin(app)
    catalog = make_catalog(app)

    unknown_plan = admin.post(URL, template_payload(catalog, plan_id=99999))
    assert_error(unknown_plan, 422, "validation_error")
    assert "plan_id" in unknown_plan.get_json()["error"]["fields"]

    payload = template_payload(catalog)
    payload["lines"][0].update(product_id=99999, tax_id=99999, variant_id=None)
    unknown_line = admin.post(URL, payload)
    assert_error(unknown_line, 422, "validation_error")
    line_errors = unknown_line.get_json()["error"]["fields"]["lines"]["0"]
    assert set(line_errors) == {"product_id", "tax_id"}


def test_quantity_must_meet_the_plan_minimum(app):
    admin = make_admin(app)
    catalog = make_catalog(app, {"min_quantity": 5})

    response = admin.post(URL, template_payload(catalog))

    assert_error(response, 422, "validation_error")
    assert "quantity" in response.get_json()["error"]["fields"]["lines"]["0"]


def test_template_needs_at_least_one_line_and_positive_validity(app):
    admin = make_admin(app)
    catalog = make_catalog(app)

    assert_error(admin.post(URL, template_payload(catalog, lines=[])), 422, "validation_error")
    assert_error(
        admin.post(URL, template_payload(catalog, validity_days=0)), 422, "validation_error"
    )


def test_duplicate_template_name_is_a_conflict(app):
    admin = make_admin(app)
    catalog = make_catalog(app)
    admin.post(URL, template_payload(catalog))

    assert_error(admin.post(URL, template_payload(catalog)), 409, "name_taken")


def test_update_replaces_the_template_and_its_lines(app):
    admin = make_admin(app)
    catalog = make_catalog(app)
    template_id = admin.post(URL, template_payload(catalog)).get_json()["id"]
    new_lines = [{"product_id": catalog["other_product_id"], "quantity": 3}]

    response = admin.put(
        f"{URL}/{template_id}",
        template_payload(catalog, name="Renamed", validity_days=10, lines=new_lines),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["name"] == "Renamed"
    assert body["validity_days"] == 10
    assert [line["product_name"] for line in body["lines"]] == ["Support"]


def test_update_to_a_taken_name_is_a_conflict(app):
    admin = make_admin(app)
    catalog = make_catalog(app)
    admin.post(URL, template_payload(catalog, name="First"))
    second_id = admin.post(URL, template_payload(catalog, name="Second")).get_json()["id"]

    response = admin.put(f"{URL}/{second_id}", template_payload(catalog, name="First"))

    assert_error(response, 409, "name_taken")


def test_deactivated_template_leaves_the_default_list(app):
    admin = make_admin(app)
    catalog = make_catalog(app)
    template_id = admin.post(URL, template_payload(catalog)).get_json()["id"]

    response = admin.delete(f"{URL}/{template_id}")

    assert response.status_code == 200
    assert response.get_json()["is_active"] is False
    assert admin.get(URL).get_json()["total"] == 0
    assert admin.get(URL, query_string={"include_inactive": "true"}).get_json()["total"] == 1


def test_unknown_template_returns_404(app):
    admin = make_admin(app)

    assert_error(admin.get(f"{URL}/99999"), 404, "not_found")
    assert_error(admin.delete(f"{URL}/99999"), 404, "not_found")


def test_pagination_limits_are_enforced(app):
    admin = make_admin(app)

    assert_error(admin.get(URL, query_string={"per_page": 101}), 422, "validation_error")
    assert_error(admin.get(URL, query_string={"page": 0}), 422, "validation_error")
