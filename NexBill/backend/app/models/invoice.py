"""Invoices, invoice lines and payments.

Overdue is deliberately not a column: it is computed in queries from
status and due_date.
"""
from app.extensions import db
from app.models.base import Money, Percentage, TimestampMixin, enum_check
from app.models.enums import InvoiceStatus, PaymentMethod

# Not picked up by autogenerate, so it is created by hand in the migration.
invoice_number_seq = db.Sequence("invoice_number_seq", metadata=db.metadata)


class Invoice(TimestampMixin, db.Model):
    __tablename__ = "invoices"
    __table_args__ = (
        # Prevents double billing, even if two billing runs overlap.
        db.UniqueConstraint(
            "subscription_id", "period_start", name="uq_invoices_subscription_id_period_start"
        ),
        enum_check("status", InvoiceStatus),
        db.CheckConstraint("period_end >= period_start", name="period_end_not_before_start"),
        db.CheckConstraint("due_date >= invoice_date", name="due_date_not_before_invoice_date"),
        db.CheckConstraint("subtotal >= 0", name="subtotal_not_negative"),
        db.CheckConstraint("tax_total >= 0", name="tax_total_not_negative"),
        db.CheckConstraint("discount_total >= 0", name="discount_total_not_negative"),
        db.CheckConstraint("total >= 0", name="total_not_negative"),
        db.CheckConstraint(
            "amount_paid >= 0 AND amount_paid <= total", name="amount_paid_within_total"
        ),
        db.Index("ix_invoices_status_due_date", "status", "due_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(30), nullable=False, unique=True)
    subscription_id = db.Column(
        db.Integer,
        db.ForeignKey("subscriptions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # The customer's details as they were when the invoice was created.
    customer_snapshot = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, server_default="draft")
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    subtotal = db.Column(Money, nullable=False, server_default="0")
    tax_total = db.Column(Money, nullable=False, server_default="0")
    discount_total = db.Column(Money, nullable=False, server_default="0")
    total = db.Column(Money, nullable=False, server_default="0")
    amount_paid = db.Column(Money, nullable=False, server_default="0")
    confirmed_at = db.Column(db.DateTime(timezone=True))
    sent_at = db.Column(db.DateTime(timezone=True))
    paid_at = db.Column(db.DateTime(timezone=True))
    cancelled_at = db.Column(db.DateTime(timezone=True))

    subscription = db.relationship("Subscription")
    customer = db.relationship("Customer")
    lines = db.relationship(
        "InvoiceLine", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments = db.relationship("Payment", back_populates="invoice")


class InvoiceLine(TimestampMixin, db.Model):
    """Stores names and rates by value, so later catalog edits cannot change it."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="quantity_positive"),
        db.CheckConstraint("unit_price >= 0", name="unit_price_not_negative"),
        db.CheckConstraint("tax_rate >= 0 AND tax_rate <= 100", name="tax_rate_between_0_and_100"),
        db.CheckConstraint("tax_amount >= 0", name="tax_amount_not_negative"),
        db.CheckConstraint("discount_amount >= 0", name="discount_amount_not_negative"),
        db.CheckConstraint("line_total >= 0", name="line_total_not_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="SET NULL"), index=True
    )
    discount_id = db.Column(
        db.Integer, db.ForeignKey("discounts.id", ondelete="SET NULL"), index=True
    )
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(Money, nullable=False)
    tax_name = db.Column(db.String(100))
    tax_rate = db.Column(Percentage, nullable=False, server_default="0")
    tax_amount = db.Column(Money, nullable=False, server_default="0")
    discount_amount = db.Column(Money, nullable=False, server_default="0")
    line_total = db.Column(Money, nullable=False)

    invoice = db.relationship("Invoice", back_populates="lines")


class Payment(TimestampMixin, db.Model):
    __tablename__ = "payments"
    __table_args__ = (
        enum_check("method", PaymentMethod),
        db.CheckConstraint("amount > 0", name="amount_positive"),
        db.Index("ix_payments_invoice_id", "invoice_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer, db.ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False
    )
    recorded_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    method = db.Column(db.String(20), nullable=False)
    amount = db.Column(Money, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text)

    invoice = db.relationship("Invoice", back_populates="payments")
