"""SQLAlchemy models. Import each model here so Flask-Migrate can detect it."""
from app.models.audit import AuditLog
from app.models.catalog import (
    Discount,
    Plan,
    Product,
    ProductVariant,
    Tax,
    discount_products,
)
from app.models.invoice import Invoice, InvoiceLine, Payment, invoice_number_seq
from app.models.quotation import QuotationTemplate, TemplateLine
from app.models.subscription import (
    Subscription,
    SubscriptionLine,
    subscription_number_seq,
)
from app.models.user import Customer, PasswordResetToken, User

__all__ = [
    "AuditLog",
    "Customer",
    "Discount",
    "Invoice",
    "InvoiceLine",
    "PasswordResetToken",
    "Payment",
    "Plan",
    "Product",
    "ProductVariant",
    "QuotationTemplate",
    "Subscription",
    "SubscriptionLine",
    "Tax",
    "TemplateLine",
    "User",
    "discount_products",
    "invoice_number_seq",
    "subscription_number_seq",
]
