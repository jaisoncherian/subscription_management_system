"""Request and response schemas for authentication and staff accounts.

The password rule is enforced in the services, so it also covers the CLI.
"""
from marshmallow import EXCLUDE, Schema, fields, validate

from app.models.enums import StaffFunction

_not_blank = validate.Regexp(r"\S", error="Must not be blank.")
_full_name = fields.String(
    required=True, validate=[validate.Length(max=150), _not_blank]
)
_email = fields.Email(required=True, validate=validate.Length(max=255))
_password = fields.String(required=True, validate=validate.Length(min=1))


class RegisterSchema(Schema):
    class Meta:
        # Public endpoint: extra fields such as "role" are ignored, never used.
        unknown = EXCLUDE

    email = _email
    password = _password
    full_name = _full_name


class LoginSchema(Schema):
    email = _email
    # Refused above this length before any hashing work is done.
    password = fields.String(required=True, validate=validate.Length(min=1, max=128))


class ForgotPasswordSchema(Schema):
    email = _email


class ResetPasswordSchema(Schema):
    token = fields.String(required=True, validate=validate.Length(min=1, max=255))
    password = _password


class CreateStaffSchema(Schema):
    email = _email
    password = _password
    full_name = _full_name
    staff_function = fields.String(
        required=True, validate=validate.OneOf([f.value for f in StaffFunction])
    )


class UserSchema(Schema):
    """Deliberately has no password_hash field."""

    id = fields.Integer()
    email = fields.String()
    full_name = fields.String()
    role = fields.String()
    staff_function = fields.String()
