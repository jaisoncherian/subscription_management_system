"""Passwords, reset tokens and JWT identity."""
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from flask_jwt_extended import create_access_token

from app.core.errors import ValidationFailed
from app.extensions import jwt
from app.repositories import user_repository

PASSWORD_MIN_LENGTH_EXCLUSIVE = 8
# Argon2 cost grows with input, so very long passwords are refused.
PASSWORD_MAX_LENGTH = 128

_hasher = PasswordHasher()
# Verified against when an email is unknown, so that login takes the same
# time whether or not the account exists.
_DUMMY_HASH = _hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def burn_password_check(password: str) -> None:
    """Spend the time of a real verification, for an account that does not exist."""
    verify_password(_DUMMY_HASH, password)


def password_hash_is_outdated(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def password_rule_violations(password: str) -> list[str]:
    violations = []
    if len(password) <= PASSWORD_MIN_LENGTH_EXCLUSIVE:
        violations.append("Must be longer than 8 characters.")
    if len(password) > PASSWORD_MAX_LENGTH:
        violations.append(f"Must be at most {PASSWORD_MAX_LENGTH} characters.")
    if not any(character.isupper() for character in password):
        violations.append("Must contain an uppercase letter.")
    if not any(character.islower() for character in password):
        violations.append("Must contain a lowercase letter.")
    if not any(not c.isalnum() and not c.isspace() for c in password):
        violations.append("Must contain a special character.")
    return violations


def require_valid_password(password: str) -> None:
    violations = password_rule_violations(password)
    if violations:
        raise ValidationFailed(fields={"password": violations})


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """A plain hash is enough here: the token is long and random, so it cannot be guessed."""
    return hashlib.sha256(token.encode()).hexdigest()


def issue_access_token(user_id: int) -> str:
    return create_access_token(identity=str(user_id))


def register_jwt_callbacks() -> None:
    @jwt.user_lookup_loader
    def load_active_user(_header, payload):
        # Reading the user on every request means role changes and
        # deactivation apply immediately, not when the token expires.
        user = user_repository.get_by_id(int(payload["sub"]))
        return user if user and user.is_active else None
