"""Shared column types and helpers for the models."""
from enum import Enum

from app.extensions import db

Money = db.Numeric(12, 2)
Percentage = db.Numeric(5, 2)


class TimestampMixin:
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )


def enum_check(column: str, enum_class: type[Enum]) -> db.CheckConstraint:
    """CHECK that `column` holds one of the enum's values."""
    values = ", ".join(f"'{member.value}'" for member in enum_class)
    return db.CheckConstraint(f"{column} IN ({values})", name=f"{column}_valid")
