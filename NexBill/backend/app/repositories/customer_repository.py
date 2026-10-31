"""Queries for customers."""
from sqlalchemy.engine import Row

from app.extensions import db
from app.models.user import Customer, User


def get_by_id(customer_id: int) -> Customer | None:
    return db.session.get(Customer, customer_id)


def add(customer: Customer) -> Customer:
    db.session.add(customer)
    db.session.flush()
    return customer


def list_page(page: int, page_size: int) -> tuple[list[Row], int]:
    """One page of customers as (id, name, email) rows, and the total count.

    An outer join, because a customer with no login has no user row and must
    still be listed. user_id is unique, so the join cannot duplicate a customer.
    """
    total = db.session.scalar(
        db.select(db.func.count(Customer.id))
        .select_from(Customer)
        .outerjoin(User, Customer.user_id == User.id)
    )

    # A very large page number would overflow the database's OFFSET type. No
    # rows can exist that far along, so the page query is not needed.
    offset = (page - 1) * page_size
    if offset >= total:
        return [], total

    rows = db.session.execute(
        db.select(Customer.id, Customer.name, Customer.email)
        .select_from(Customer)
        .outerjoin(User, Customer.user_id == User.id)
        .order_by(Customer.id)
        .limit(page_size)
        .offset(offset)
    ).all()
    return list(rows), total
