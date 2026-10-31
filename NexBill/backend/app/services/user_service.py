"""Creating user accounts."""
from sqlalchemy.exc import IntegrityError

from app.core.errors import Conflict
from app.core.security import hash_password, require_valid_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories import audit_repository, transaction, user_repository

ADMIN_FULL_NAME = "Administrator"


def build_user(
    email: str,
    password: str,
    full_name: str,
    role: UserRole,
    staff_function: str | None = None,
) -> User:
    """Add a user to the current transaction. The caller commits."""
    require_valid_password(password)
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        staff_function=staff_function,
    )
    try:
        return user_repository.add(user)
    except IntegrityError:
        # Covers the race where two requests pass any earlier check together.
        transaction.rollback()
        raise Conflict(
            "An account with this email already exists.",
            code="email_taken",
            fields={"email": ["An account with this email already exists."]},
        ) from None


def create_staff(
    actor_user_id: int, email: str, password: str, full_name: str, staff_function: str
) -> User:
    user = build_user(email, password, full_name, UserRole.STAFF, staff_function)
    audit_repository.record(
        "staff.created",
        "user",
        user.id,
        actor_user_id,
        {"staff_function": staff_function},
    )
    transaction.commit()
    return user


def list_staff(page: int, page_size: int) -> tuple[list[User], int]:
    return user_repository.list_by_role(UserRole.STAFF, page, page_size)


def ensure_admin(email: str, password: str) -> tuple[User, bool]:
    """Create the admin once. Returns the user and whether it was just created.

    An existing admin keeps their current password.
    """
    existing = user_repository.get_by_email(email)
    if existing:
        if existing.role != UserRole.ADMIN:
            raise Conflict(
                f"This email already belongs to a {existing.role} account.",
                code="email_taken",
            )
        return existing, False

    user = build_user(email, password, ADMIN_FULL_NAME, UserRole.ADMIN)
    audit_repository.record("admin.created", "user", user.id)
    transaction.commit()
    return user, True
