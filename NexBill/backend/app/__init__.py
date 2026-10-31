"""NexBill application factory."""
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import REQUIRED_SETTINGS, get_config
from app.core.errors import register_error_handlers
from app.core.http import register_security_headers
from app.core.logging import configure_logging, register_request_logging
from app.core.security import register_jwt_callbacks
from app.extensions import db, jwt, limiter, migrate
from app.jobs import register_commands
from app.routes import register_blueprints
from app.routes.frontend import register_frontend


def create_app(config_name: str | None = None) -> Flask:
    """Build the app. config_name falls back to APP_ENV, then "development"."""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    _require_settings(app)
    if app.config["IS_PRODUCTION"]:
        _require_production_settings(app)
    if app.config["TRUSTED_PROXY_COUNT"]:
        count = app.config["TRUSTED_PROXY_COUNT"]
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=count, x_proto=count, x_host=count)

    configure_logging(app)
    register_request_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # Imported so Flask-Migrate can see every model during autogenerate.
    from app import models  # noqa: F401

    register_error_handlers(app)
    register_security_headers(app)
    register_jwt_callbacks()
    register_blueprints(app)
    register_commands(app)
    # Last, because its catch-all route must not hide any other route.
    register_frontend(app)
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


def _require_production_settings(app: Flask) -> None:
    """Refuse to go live on demo secrets, rather than fail quietly later."""
    problems = []
    for setting in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = app.config[setting]
        if "change-me" in value or len(value) < 32:
            problems.append(f"{setting} must be a random value of at least 32 characters")
    if "change-me" in app.config["SQLALCHEMY_DATABASE_URI"]:
        problems.append("DATABASE_URL still has the example password")
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        problems.append("DATABASE_URL must point at PostgreSQL")
    if not app.config["FRONTEND_URL"]:
        problems.append("FRONTEND_URL must be set, because reset emails link to it")
    if problems:
        raise RuntimeError("Not safe for production: " + "; ".join(problems) + ".")
