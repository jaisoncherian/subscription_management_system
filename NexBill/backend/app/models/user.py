"""Accounts: users, customers and password reset tokens."""
from sqlalchemy.orm import validates

from app.extensions import db
from app.models.base import TimestampMixin, enum_check
from app.models.enums import StaffFunction, UserRole


def _normalize_email(email: str | None) -> str | None:
    return email.strip().lower() if email else email


class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        enum_check("role", UserRole),
        enum_check("staff_function", StaffFunction),
        db.CheckConstraint("email = lower(email)", name="email_lowercase"),
        db.CheckConstraint(
            "(role = 'staff' AND staff_function IS NOT NULL) "
            "OR (role <> 'staff' AND staff_function IS NULL)",
            name="staff_function_only_for_staff",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    staff_function = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())

    customer = db.relationship("Customer", back_populates="user", uselist=False)

    @validates("email")
    def _lowercase_email(self, _key, email):
        return _normalize_email(email)


class Customer(TimestampMixin, db.Model):
    """A billable party. user_id is empty until the customer has a login."""

    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(30))
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    tax_identifier = db.Column(db.String(50))

    user = db.relationship("User", back_populates="customer")

    @validates("email")
    def _lowercase_email(self, _key, email):
        return _normalize_email(email)


class PasswordResetToken(db.Model):
    """Only the hash of a reset token is stored, never the token itself."""

    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )
