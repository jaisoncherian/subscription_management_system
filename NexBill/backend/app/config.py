"""Environment-driven configuration."""
import os
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


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key-not-used-outside-pytest"
    JWT_SECRET_KEY = "test-jwt-secret-key-not-used-outside-pytest"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    pass


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
