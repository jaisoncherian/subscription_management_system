"""Environment-driven configuration."""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# NexBill/.env, regardless of the working directory. Real environment variables win.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Flask setting -> environment variable that provides it.
REQUIRED_SETTINGS = {
    "SECRET_KEY": "SECRET_KEY",
    "JWT_SECRET_KEY": "JWT_SECRET_KEY",
    "SQLALCHEMY_DATABASE_URI": "DATABASE_URL",
}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    DEBUG = False
    TESTING = False

    # The JWT lives in an httpOnly cookie, so browser JavaScript cannot read it.
    # CSRF protection is on because cookies are sent automatically.
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_SECURE = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    # Used to build the link in password reset emails.
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Without SMTP_HOST, email goes to MAIL_OUTBOX_DIR if set, otherwise nowhere.
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@brightloop.example")
    MAIL_OUTBOX_DIR = None


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_OUTBOX_DIR = str(Path(__file__).resolve().parents[1] / "dev_outbox")


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key-not-used-outside-pytest"
    JWT_SECRET_KEY = "test-jwt-secret-key-not-used-outside-pytest"
    # Set TEST_DATABASE_URL to run on PostgreSQL. Row locks and SKIP LOCKED
    # only behave for real there; SQLite is the zero-setup fallback.
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    JWT_COOKIE_SECURE = True


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    name = name or os.getenv("APP_ENV", "development")
    try:
        return _CONFIGS[name]
    except KeyError:
        raise ValueError(
            f"Unknown config {name!r}. Expected one of: {', '.join(_CONFIGS)}"
        ) from None
