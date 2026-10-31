"""NexBill application factory."""
from flask import Flask

from app.config import REQUIRED_SETTINGS, get_config
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging, register_request_logging
from app.core.security import register_jwt_callbacks
from app.extensions import db, jwt, limiter, migrate
from app.jobs import register_commands
from app.routes import register_blueprints


def create_app(config_name: str | None = None) -> Flask:
    """Build the app. config_name falls back to APP_ENV, then "development"."""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    _require_settings(app)

    configure_logging(app)
    register_request_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # Imported so Flask-Migrate can see every model during autogenerate.
    from app import models  # noqa: F401

    register_error_handlers(app)
    register_jwt_callbacks()
    register_blueprints(app)
    register_commands(app)
    return app


def _require_settings(app: Flask) -> None:
    missing = [
        env_var
        for setting, env_var in REQUIRED_SETTINGS.items()
        if not app.config.get(setting)
    ]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )
