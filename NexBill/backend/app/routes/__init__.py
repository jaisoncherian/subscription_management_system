"""HTTP routes."""
from flask import Flask

from app.routes.health import health_bp
from app.routes.reports import reports_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(reports_bp)
