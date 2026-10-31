"""Registration, login and password reset."""
from datetime import datetime, timedelta, timezone

from flask import current_app

from app.core.errors import AppError, Unauthorized
from app.core.security import (
    burn_password_check,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    issue_access_token,
    password_hash_is_outdated,
    require_valid_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import Customer, PasswordResetToken, User
from app.repositories import (
    audit_repository,
    customer_repository,
    password_reset_repository,
    transaction,
    user_repository,
)
from app.services import mail_service, user_service

RESET_TOKEN_LIFETIME = timedelta(minutes=30)


def register_customer(email: str, password: str, full_name: str) -> User:
    """Public signup. The role is fixed here, so a request can never choose it."""
    user = user_service.build_user(email, password, full_name, UserRole.CUSTOMER)
    customer_repository.add(Customer(user_id=user.id, name=full_name, email=email))
    audit_repository.record("user.registered", "user", user.id, user.id)
    transaction.commit()
    return user


def login(email: str, password: str) -> tuple[User, str]:
    """Return the user and an access token.

    Every failure looks the same, so login cannot reveal which emails exist.
    """
    user = user_repository.get_by_email(email)
    if user is None:
        burn_password_check(password)
        raise _invalid_credentials()
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise _invalid_credentials()

    if password_hash_is_outdated(user.password_hash):
        user.password_hash = hash_password(password)
    audit_repository.record("user.logged_in", "user", user.id, user.id)
    transaction.commit()
    return user, issue_access_token(user.id)


def request_password_reset(email: str) -> None:
    """Does nothing visible for an unknown or inactive email. The route's reply is the same."""
    user = user_repository.get_by_email(email)
    if user is None or not user.is_active:
        return

    now = datetime.now(timezone.utc)
    token = generate_reset_token()
    password_reset_repository.retire_unused_for_user(user.id, now)
    password_reset_repository.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_reset_token(token),
            expires_at=now + RESET_TOKEN_LIFETIME,
        )
    )
    audit_repository.record("user.password_reset_requested", "user", user.id, user.id)
    transaction.commit()

    link = f"{current_app.config['FRONTEND_URL']}/reset-password?token={token}"
    mail_service.send_email(
        user.email,
        "Reset your password",
        f"Use this link to reset your password. It expires in 30 minutes "
        f"and works once.\n\n{link}\n\n"
        "If you did not ask for this, you can ignore this email.",
    )


def reset_password(token: str, new_password: str) -> None:
    require_valid_password(new_password)

    now = datetime.now(timezone.utc)
    reset_token = password_reset_repository.get_usable_for_update(
        hash_reset_token(token), now
    )
    user = reset_token and user_repository.get_by_id(reset_token.user_id)
    if not user or not user.is_active:
        raise AppError(
            "This reset link is invalid or has expired.", code="invalid_reset_token"
        )

    user.password_hash = hash_password(new_password)
    # Also spends this token, and any other link that was still outstanding.
    password_reset_repository.retire_unused_for_user(user.id, now)
    audit_repository.record("user.password_reset_completed", "user", user.id, user.id)
    transaction.commit()


def _invalid_credentials() -> Unauthorized:
    return Unauthorized("Incorrect email or password.", code="invalid_credentials")
