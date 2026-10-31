"""HTTP routes."""
from flask import Flask

from app.routes.auth import auth_bp
from app.routes.health import health_bp
from app.routes.quotation_templates import quotation_templates_bp
from app.routes.staff import staff_bp
from app.routes.subscriptions import subscriptions_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(quotation_templates_bp)
    app.register_blueprint(subscriptions_bp)
