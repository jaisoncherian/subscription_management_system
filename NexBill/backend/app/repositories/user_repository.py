"""Queries for users."""
from app.extensions import db
from app.models.user import User, normalize_email


def get_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def get_by_email(email: str) -> User | None:
    return db.session.scalar(
        db.select(User).where(User.email == normalize_email(email))
    )


def add(user: User) -> User:
    """Raises IntegrityError if the email is already taken."""
    db.session.add(user)
    db.session.flush()
    return user
