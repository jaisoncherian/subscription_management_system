"""Queries for users."""
from app.extensions import db
from app.models.user import Customer, User, normalize_email


def get_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def get_by_email(email: str) -> User | None:
    return db.session.scalar(
        db.select(User).where(User.email == normalize_email(email))
    )


def list_by_role(role: str, page: int, page_size: int) -> tuple[list[User], int]:
    result = db.paginate(
        db.select(User).where(User.role == role).order_by(User.id),
        page=page,
        per_page=page_size,
        error_out=False,
    )
    return result.items, result.total


def get_customer_for_user(user_id: int) -> Customer | None:
    return db.session.scalar(db.select(Customer).where(Customer.user_id == user_id))


def add(user: User) -> User:
    """Raises IntegrityError if the email is already taken."""
    db.session.add(user)
    db.session.flush()
    return user
