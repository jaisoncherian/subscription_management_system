"""Queries for password reset tokens."""
from datetime import datetime

from app.extensions import db
from app.models.user import PasswordResetToken


def add(token: PasswordResetToken) -> PasswordResetToken:
    db.session.add(token)
    db.session.flush()
    return token


def get_usable_for_update(token_hash: str, now: datetime) -> PasswordResetToken | None:
    """Lock an unused, unexpired token.

    A concurrent request waits on the lock, then finds the token already used,
    so a token can only ever be spent once.
    """
    return db.session.scalar(
        db.select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .with_for_update()
    )


def retire_unused_for_user(user_id: int, now: datetime) -> None:
    db.session.execute(
        db.update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
