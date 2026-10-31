"""Authentication, RBAC and the rules that protect them."""
import logging
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import hash_reset_token
from app.extensions import db
from app.models import AuditLog, Customer, PasswordResetToken, User
from app.models.enums import UserRole
from app.services import mail_service, user_service

GOOD_PASSWORD = "Str0ng!Password"
NEW_PASSWORD = "An0ther!Password"


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.get_json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "fields"}
    assert body["error"]["code"] == code


def register(client, email="ana@example.com", password=GOOD_PASSWORD, **extra):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Ana", **extra},
    )


def login(client, email="ana@example.com", password=GOOD_PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def csrf_headers(client):
    return {"X-CSRF-TOKEN": client.get_cookie("csrf_access_token").value}


def create_staff_payload(email="sam@example.com"):
    return {
        "email": email,
        "password": GOOD_PASSWORD,
        "full_name": "Sam",
        "staff_function": "sales_rep",
    }


def login_as_admin(app, client):
    with app.app_context():
        user_service.ensure_admin("admin@example.com", GOOD_PASSWORD)
    assert login(client, "admin@example.com").status_code == 200


@pytest.fixture
def sent_emails(monkeypatch):
    emails = []
    monkeypatch.setattr(
        mail_service,
        "send_email",
        lambda to, subject, body: emails.append({"to": to, "body": body}),
    )
    return emails


def token_from(email):
    return email["body"].split("token=")[1].split()[0]


# Registration


def test_register_creates_a_customer_with_a_customer_record(app, client):
    response = register(client)

    assert response.status_code == 201
    assert response.get_json()["role"] == "customer"
    assert "password_hash" not in response.get_json()
    with app.app_context():
        user = db.session.scalar(db.select(User))
        customer = db.session.scalar(db.select(Customer))
        assert customer.user_id == user.id
        assert user.password_hash != GOOD_PASSWORD


@pytest.mark.parametrize(
    "extra", [{"role": "admin"}, {"role": "staff", "staff_function": "support"}]
)
def test_register_cannot_choose_a_role(client, extra):
    response = register(client, **extra)

    assert response.status_code == 201
    assert response.get_json()["role"] == "customer"
    assert response.get_json()["staff_function"] is None


def test_register_stores_the_email_lowercase(client):
    assert register(client, email="Ana@Example.COM").get_json()["email"] == "ana@example.com"


def test_register_rejects_a_duplicate_email_ignoring_case(client):
    register(client)

    assert_error(register(client, email="ANA@example.com"), 409, "email_taken")


def test_failed_registration_leaves_nothing_behind(app, client):
    register(client)
    register(client, email="ANA@example.com")

    with app.app_context():
        assert len(db.session.scalars(db.select(Customer)).all()) == 1


def test_password_of_nine_characters_is_accepted(client):
    assert register(client, password="Sh0rt!pwd").status_code == 201


@pytest.mark.parametrize(
    "password, reason",
    [
        ("Sh0rt!pw", "exactly 8 characters"),
        ("alllower!case1", "no uppercase"),
        ("ALLUPPER!CASE1", "no lowercase"),
        ("NoSpecialChar1", "no special character"),
        ("Spaces Only Here", "a space is not a special character"),
        ("Aa!" + "x" * 126, "longer than 128 characters"),
    ],
)
def test_password_rule_rejects(client, password, reason):
    response = register(client, password=password)

    assert_error(response, 422, "validation_error")
    assert "password" in response.get_json()["error"]["fields"], reason


@pytest.mark.parametrize(
    "body",
    [{}, {"email": "not-an-email", "password": GOOD_PASSWORD, "full_name": "Ana"},
     {"email": "a@example.com", "password": GOOD_PASSWORD, "full_name": "   "}],
)
def test_register_validates_input(client, body):
    assert_error(client.post("/api/auth/register", json=body), 422, "validation_error")


def test_a_non_object_json_body_returns_a_validation_error(client):
    assert_error(client.post("/api/auth/register", json=[1, 2]), 422, "validation_error")


# Login


def test_login_returns_the_role_from_the_database_and_sets_cookies(client):
    register(client)

    response = login(client)

    assert response.status_code == 200
    assert response.get_json()["role"] == "customer"
    cookies = response.headers.getlist("Set-Cookie")
    access_cookie = next(c for c in cookies if c.startswith("access_token_cookie="))
    assert "HttpOnly" in access_cookie
    assert "SameSite=Lax" in access_cookie
    assert "access_token" not in response.get_data(as_text=True)


def test_login_accepts_any_email_case(client):
    register(client)

    assert login(client, email="ANA@EXAMPLE.COM").status_code == 200


def test_wrong_password_and_unknown_email_look_identical(client):
    register(client)

    wrong_password = login(client, password="Wr0ng!Password")
    unknown_email = login(client, email="nobody@example.com")

    assert_error(wrong_password, 401, "invalid_credentials")
    assert wrong_password.get_json() == unknown_email.get_json()


def test_inactive_user_cannot_log_in(app, client):
    register(client)
    with app.app_context():
        db.session.scalar(db.select(User)).is_active = False
        db.session.commit()

    assert_error(login(client), 401, "invalid_credentials")


def test_me_returns_the_logged_in_user(client):
    register(client)
    login(client)

    assert client.get("/api/auth/me").get_json()["email"] == "ana@example.com"


def test_me_without_a_cookie_is_rejected(client):
    assert_error(client.get("/api/auth/me"), 401, "unauthorized")


def test_logout_clears_the_session(client):
    register(client)
    login(client)

    assert client.post("/api/auth/logout").status_code == 200

    assert_error(client.get("/api/auth/me"), 401, "unauthorized")


def test_deactivating_a_user_ends_their_session_immediately(app, client):
    register(client)
    login(client)
    with app.app_context():
        db.session.scalar(db.select(User)).is_active = False
        db.session.commit()

    assert_error(client.get("/api/auth/me"), 401, "unauthorized")


# Password reset


def test_forgot_password_gives_the_same_reply_for_any_email(client, sent_emails):
    register(client)

    known = client.post("/api/auth/forgot-password", json={"email": "ana@example.com"})
    unknown = client.post("/api/auth/forgot-password", json={"email": "no@example.com"})

    assert known.status_code == unknown.status_code == 200
    assert known.get_json() == unknown.get_json()
    assert [email["to"] for email in sent_emails] == ["ana@example.com"]


def test_inactive_user_gets_no_reset_email(app, client, sent_emails):
    register(client)
    with app.app_context():
        db.session.scalar(db.select(User)).is_active = False
        db.session.commit()

    response = client.post("/api/auth/forgot-password", json={"email": "ana@example.com"})

    assert response.status_code == 200
    assert sent_emails == []


def request_token(client, sent_emails):
    client.post("/api/auth/forgot-password", json={"email": "ana@example.com"})
    return token_from(sent_emails[-1])


def reset(client, token, password=NEW_PASSWORD):
    return client.post(
        "/api/auth/reset-password", json={"token": token, "password": password}
    )


def test_reset_token_is_stored_hashed_and_lasts_30_minutes(app, client, sent_emails):
    register(client)
    token = request_token(client, sent_emails)

    with app.app_context():
        stored = db.session.scalar(db.select(PasswordResetToken))
        assert stored.token_hash == hash_reset_token(token)
        assert stored.token_hash != token
        lifetime = stored.expires_at - stored.created_at
        assert timedelta(minutes=29) < lifetime < timedelta(minutes=31)


def test_reset_changes_the_password(client, sent_emails):
    register(client)
    token = request_token(client, sent_emails)

    assert reset(client, token).status_code == 200

    assert_error(login(client), 401, "invalid_credentials")
    assert login(client, password=NEW_PASSWORD).status_code == 200


def test_reset_token_works_only_once(client, sent_emails):
    register(client)
    token = request_token(client, sent_emails)
    reset(client, token)

    assert_error(reset(client, token, "Th1rd!Password"), 400, "invalid_reset_token")
    assert login(client, password=NEW_PASSWORD).status_code == 200


def test_expired_reset_token_is_rejected(app, client, sent_emails):
    register(client)
    token = request_token(client, sent_emails)
    with app.app_context():
        stored = db.session.scalar(db.select(PasswordResetToken))
        stored.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.session.commit()

    assert_error(reset(client, token), 400, "invalid_reset_token")


def test_unknown_reset_token_is_rejected(client):
    assert_error(reset(client, "made-up-token"), 400, "invalid_reset_token")


def test_requesting_a_new_link_retires_the_old_one(client, sent_emails):
    register(client)
    old_token = request_token(client, sent_emails)
    new_token = request_token(client, sent_emails)

    assert_error(reset(client, old_token), 400, "invalid_reset_token")
    assert reset(client, new_token).status_code == 200


def test_reset_enforces_the_password_rule_without_spending_the_token(client, sent_emails):
    register(client)
    token = request_token(client, sent_emails)

    assert_error(reset(client, token, "weak"), 422, "validation_error")
    assert reset(client, token).status_code == 200


# Staff and RBAC


def test_admin_can_create_staff(app, client):
    login_as_admin(app, client)

    response = client.post(
        "/api/staff", json=create_staff_payload(), headers=csrf_headers(client)
    )

    assert response.status_code == 201
    assert response.get_json()["role"] == "staff"
    assert response.get_json()["staff_function"] == "sales_rep"
    with app.app_context():
        audit = db.session.scalar(
            db.select(AuditLog).where(AuditLog.action == "staff.created")
        )
        assert audit is not None
        assert GOOD_PASSWORD not in str(audit.details)


def test_customer_cannot_create_staff(client):
    register(client)
    login(client)

    response = client.post(
        "/api/staff", json=create_staff_payload(), headers=csrf_headers(client)
    )

    assert_error(response, 403, "forbidden")


def test_staff_cannot_create_staff(app, client):
    with app.app_context():
        user_service.create_staff(None, "sam@example.com", GOOD_PASSWORD, "Sam", "support")
    login(client, "sam@example.com")

    response = client.post(
        "/api/staff", json=create_staff_payload("new@example.com"), headers=csrf_headers(client)
    )

    assert_error(response, 403, "forbidden")


def test_creating_staff_requires_login(client):
    assert_error(client.post("/api/staff", json=create_staff_payload()), 401, "unauthorized")


def test_creating_staff_requires_the_csrf_header(app, client):
    login_as_admin(app, client)

    assert_error(client.post("/api/staff", json=create_staff_payload()), 401, "unauthorized")


def test_create_staff_validates_the_function(app, client):
    login_as_admin(app, client)
    payload = create_staff_payload() | {"staff_function": "wizard"}

    response = client.post("/api/staff", json=payload, headers=csrf_headers(client))

    assert_error(response, 422, "validation_error")


def test_demoted_admin_loses_access_immediately(app, client):
    login_as_admin(app, client)
    with app.app_context():
        user = db.session.scalar(db.select(User))
        user.role = UserRole.CUSTOMER
        db.session.commit()

    response = client.post(
        "/api/staff", json=create_staff_payload(), headers=csrf_headers(client)
    )

    assert_error(response, 403, "forbidden")


# create-admin command


def run_create_admin(app, email="boss@example.com", password=GOOD_PASSWORD):
    app.config.update(ADMIN_EMAIL=email, ADMIN_PASSWORD=password)
    return app.test_cli_runner().invoke(args=["create-admin"])


def test_create_admin_creates_an_admin_who_can_log_in(app, client):
    result = run_create_admin(app)

    assert result.exit_code == 0
    assert login(client, "boss@example.com").get_json()["role"] == "admin"
    assert GOOD_PASSWORD not in result.output


def test_create_admin_twice_keeps_the_original_password(app, client):
    run_create_admin(app)

    result = run_create_admin(app, password=NEW_PASSWORD)

    assert result.exit_code == 0
    assert "already exists" in result.output
    assert login(client, "boss@example.com").status_code == 200


def test_create_admin_rejects_a_weak_password(app):
    result = run_create_admin(app, password="weak")

    assert result.exit_code != 0
    assert "uppercase" in result.output
    assert "weak" not in result.output


def test_create_admin_requires_credentials(app):
    result = run_create_admin(app, email=None, password=None)

    assert result.exit_code != 0
    assert "ADMIN_EMAIL" in result.output


def test_create_admin_refuses_an_email_owned_by_a_customer(app, client):
    register(client, email="boss@example.com")

    result = run_create_admin(app)

    assert result.exit_code != 0
    assert login(client, "boss@example.com").get_json()["role"] == "customer"


# Rate limiting and logging


def test_login_is_rate_limited(rate_limited_app):
    client = rate_limited_app.test_client()

    responses = [login(client, "no@example.com") for _ in range(6)]

    assert [r.status_code for r in responses[:5]] == [401] * 5
    assert_error(responses[5], 429, "too_many_requests")


def test_reset_password_is_rate_limited(rate_limited_app):
    client = rate_limited_app.test_client()

    responses = [reset(client, "made-up-token") for _ in range(6)]

    assert [r.status_code for r in responses[:5]] == [400] * 5
    assert_error(responses[5], 429, "too_many_requests")


def test_forgot_password_is_rate_limited(rate_limited_app):
    client = rate_limited_app.test_client()

    responses = [
        client.post("/api/auth/forgot-password", json={"email": "no@example.com"})
        for _ in range(6)
    ]

    assert [r.status_code for r in responses[:5]] == [200] * 5
    assert_error(responses[5], 429, "too_many_requests")


def test_passwords_and_tokens_are_never_logged(client, sent_emails, caplog):
    with caplog.at_level(logging.DEBUG):
        register(client)
        login(client)
        token = request_token(client, sent_emails)
        reset(client, token)

    assert caplog.records
    assert GOOD_PASSWORD not in caplog.text
    assert NEW_PASSWORD not in caplog.text
    assert token not in caplog.text


def test_mail_delivery_failure_does_not_log_the_message(caplog):
    settings = {
        "host": "127.0.0.1",
        "port": 1,
        "username": None,
        "password": None,
        "outbox_dir": None,
    }
    message = mail_service.EmailMessage()
    message["To"] = "ana@example.com"
    message.set_content("token=secret-value")

    with caplog.at_level(logging.DEBUG):
        mail_service._deliver(message, settings)

    assert "email delivery failed" in caplog.text
    assert "secret-value" not in caplog.text


def test_development_outbox_keeps_long_links_intact(tmp_path):
    link = "http://localhost:5173/reset-password?token=" + "a" * 100
    message = mail_service.EmailMessage()
    message["To"] = "ana@example.com"
    message["Subject"] = "Reset"
    message.set_content(f"Use this link.\n\n{link}\n")

    settings = {
        "host": None,
        "port": 587,
        "username": None,
        "password": None,
        "outbox_dir": str(tmp_path / "outbox"),
    }
    mail_service._deliver(message, settings)

    files = list((tmp_path / "outbox").iterdir())
    assert len(files) == 1
    assert link in files[0].read_text(encoding="utf-8")


def test_user_responses_expose_only_the_public_fields(client):
    body = register(client).get_json()

    assert set(body) == {"id", "email", "full_name", "role", "staff_function"}


def test_login_is_recorded_in_the_audit_log(app, client):
    register(client)
    login(client)

    with app.app_context():
        actions = db.session.scalars(db.select(AuditLog.action)).all()
    assert "user.logged_in" in actions
