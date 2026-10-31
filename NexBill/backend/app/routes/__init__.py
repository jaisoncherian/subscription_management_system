"""HTTP routes."""
from flask import Flask

from app.routes.auth import auth_bp
from app.routes.billing import billing_bp
from app.routes.catalog import catalog_bp
from app.routes.customers import customers_bp
from app.routes.health import health_bp
from app.routes.invoices import invoices_bp
from app.routes.payments import payments_bp
from app.routes.portal import portal_bp
from app.routes.quotation_templates import quotation_templates_bp
from app.routes.reports import reports_bp
from app.routes.staff import staff_bp
from app.routes.subscriptions import subscriptions_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(quotation_templates_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(reports_bp)
