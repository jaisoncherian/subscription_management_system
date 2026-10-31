"""GET /api/customers."""
import pytest
from sqlalchemy import event

from app.extensions import db
from app.models import Customer
from app.repositories import customer_repository
from helpers import ApiClient, assert_error, make_admin, make_customer, make_staff

URL = "/api/customers"


def add_customers(app, count):
    """Returns the new customers' ids, in order."""
    with app.app_context():
        customers = [
            Customer(name=f"Customer {number}", email=f"customer{number}@example.com")
            for number in range(1, count + 1)
        ]
        db.session.add_all(customers)
        db.session.commit()
        return [customer.id for customer in customers]


def test_admin_gets_the_list_with_the_correct_item_shape(app):
    admin = make_admin(app)
    [customer_id] = add_customers(app, 1)

    response = admin.get(URL)

    assert response.status_code == 200
    assert response.get_json() == {
        "items": [
            {"id": customer_id, "name": "Customer 1", "email": "customer1@example.com"}
        ],
        "page": 1,
        "page_size": 20,
        "total": 1,
    }


def test_staff_gets_the_list(app):
    add_customers(app, 1)

    response = make_staff(app).get(URL)

    assert response.status_code == 200
    assert response.get_json()["total"] == 1


def test_customer_role_is_forbidden(app):
    client, _ = make_customer(app)

    assert_error(client.get(URL), 403, "forbidden")


def test_login_is_required(app):
    assert_error(ApiClient(app).get(URL), 401, "unauthorized")


def test_id_is_the_customer_id_not_the_user_id(app):
    admin = make_admin(app)
    add_customers(app, 1)
    _, customer_id = make_customer(app, "real@example.com", "Real Customer")

    items = admin.get(URL).get_json()["items"]

    assert {"id": customer_id, "name": "Real Customer", "email": "real@example.com"} in items


def test_customer_without_a_login_is_still_listed(app):
    admin = make_admin(app)
    [customer_id] = add_customers(app, 1)
    with app.app_context():
        assert db.session.get(Customer, customer_id).user_id is None

    assert [item["id"] for item in admin.get(URL).get_json()["items"]] == [customer_id]


def test_pagination_returns_the_requested_slice_in_id_order(app):
    admin = make_admin(app)
    ids = add_customers(app, 5)

    body = admin.get(URL, query_string={"page": 2, "page_size": 2}).get_json()

    assert [item["id"] for item in body["items"]] == ids[2:4]
    assert body["page"] == 2
    assert body["page_size"] == 2
    assert body["total"] == 5


@pytest.mark.parametrize(
    "params, field",
    [
        ({"page": 0}, "page"),
        ({"page": -1}, "page"),
        ({"page": "abc"}, "page"),
        ({"page_size": 0}, "page_size"),
        ({"page_size": "abc"}, "page_size"),
        ({"page_size": 101}, "page_size"),
    ],
)
def test_invalid_params_return_422_naming_the_field(app, params, field):
    response = make_admin(app).get(URL, query_string=params)

    assert_error(response, 422, "validation_error")
    error = response.get_json()["error"]
    assert error["message"] == "Invalid input"
    assert list(error["fields"]) == [field]
    assert error["fields"][field]


def test_page_size_of_100_is_accepted(app):
    response = make_admin(app).get(URL, query_string={"page_size": 100})

    assert response.status_code == 200
    assert response.get_json()["page_size"] == 100


def test_empty_table_returns_an_empty_page(app):
    response = make_admin(app).get(URL)

    assert response.status_code == 200
    assert response.get_json() == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_page_past_the_end_returns_no_items_and_the_real_total(app):
    admin = make_admin(app)
    add_customers(app, 3)

    body = admin.get(URL, query_string={"page": 2, "page_size": 20}).get_json()

    assert body["items"] == []
    assert body["total"] == 3


def test_enormous_page_number_does_not_overflow_the_database(app):
    admin = make_admin(app)
    add_customers(app, 1)

    response = admin.get(URL, query_string={"page": 10**30})

    assert response.status_code == 200
    assert response.get_json()["items"] == []


def test_items_expose_only_id_name_and_email(app):
    admin = make_admin(app)
    make_customer(app)

    response = admin.get(URL)

    assert set(response.get_json()["items"][0]) == {"id", "name", "email"}
    assert "password_hash" not in response.get_data(as_text=True)


def test_unknown_params_are_ignored(app):
    admin = make_admin(app)
    add_customers(app, 2)

    response = admin.get(URL, query_string={"customer_id": 1, "role": "admin"})

    assert response.status_code == 200
    assert response.get_json()["total"] == 2


def test_repository_runs_one_count_query_and_one_page_query(app):
    add_customers(app, 5)
    statements = []

    def capture(_conn, _cursor, statement, *_args):
        statements.append(statement)

    with app.app_context():
        event.listen(db.engine, "before_cursor_execute", capture)
        try:
            rows, total = customer_repository.list_page(1, 3)
            # Reading every value must not trigger any further queries.
            values = [(row.id, row.name, row.email) for row in rows]
        finally:
            event.remove(db.engine, "before_cursor_execute", capture)

    assert len(statements) == 2
    assert "count(" in statements[0].lower()
    assert "limit" in statements[1].lower()
    assert total == 5
    assert len(values) == 3
