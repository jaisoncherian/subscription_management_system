"""Allowed values for status and type columns.

Columns store the plain string value, guarded by a CHECK constraint. Adding a
value later only needs a new constraint, not a PostgreSQL enum type change.
"""
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


class StaffFunction(StrEnum):
    SALES_REP = "sales_rep"
    FINANCE_LEAD = "finance_lead"
    SUPPORT = "support"


class ProductType(StrEnum):
    SERVICE = "service"
    GOODS = "goods"


class BillingPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class DiscountType(StrEnum):
    PERCENT = "percent"
    FIXED = "fixed"


class DiscountScope(StrEnum):
    PRODUCT = "product"
    SUBSCRIPTION = "subscription"


class SubscriptionStatus(StrEnum):
    DRAFT = "draft"
    QUOTATION = "quotation"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    OTHER = "other"
