"""Password hashing helpers built on Argon2."""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return a salted Argon2 hash for a plaintext password."""
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return True when a plaintext password matches a stored Argon2 hash."""
    if not isinstance(password, str) or not isinstance(password_hash, str):
        return False

    try:
        _password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError, TypeError):
        return False
    return True
