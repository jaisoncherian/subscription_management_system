"""Customers."""
from collections.abc import Mapping

from marshmallow import ValidationError

from app.core.errors import ValidationFailed
from app.repositories import customer_repository
from app.schemas.customer import CustomerListQuerySchema


def list_customers(params: Mapping[str, str]) -> dict:
    try:
        query = CustomerListQuerySchema().load(params)
    except ValidationError as error:
        raise ValidationFailed(
            "Invalid input", fields=error.normalized_messages()
        ) from None

    items, total = customer_repository.list_page(query["page"], query["page_size"])
    return {
        "items": items,
        "page": query["page"],
        "page_size": query["page_size"],
        "total": total,
    }
