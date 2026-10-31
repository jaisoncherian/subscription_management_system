"""Queries for customers."""
from app.extensions import db
from app.models.user import Customer


def get_by_id(customer_id: int) -> Customer | None:
    return db.session.get(Customer, customer_id)


def add(customer: Customer) -> Customer:
    db.session.add(customer)
    db.session.flush()
    return customer
