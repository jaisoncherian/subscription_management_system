"""Subscriptions and their lines."""
from app.extensions import db
from app.models.base import Money, TimestampMixin, enum_check
from app.models.enums import SubscriptionStatus

# Not picked up by autogenerate, so it is created by hand in the migration.
subscription_number_seq = db.Sequence("subscription_number_seq", metadata=db.metadata)


class Subscription(TimestampMixin, db.Model):
    __tablename__ = "subscriptions"
    __table_args__ = (
        enum_check("status", SubscriptionStatus),
        # The billing run depends on every active subscription having a date.
        db.CheckConstraint(
            "status <> 'active' OR next_billing_date IS NOT NULL",
            name="active_has_next_billing_date",
        ),
        db.CheckConstraint("expires_on >= start_date", name="expires_on_not_before_start"),
        db.Index(
            "ix_subscriptions_next_billing_date_active",
            "next_billing_date",
            postgresql_where=db.text("status = 'active'"),
            sqlite_where=db.text("status = 'active'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    subscription_number = db.Column(db.String(30), nullable=False, unique=True)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    template_id = db.Column(
        db.Integer,
        db.ForeignKey("quotation_templates.id", ondelete="SET NULL"),
        index=True,
    )
    discount_id = db.Column(
        db.Integer, db.ForeignKey("discounts.id", ondelete="RESTRICT"), index=True
    )
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    status = db.Column(
        db.String(20), nullable=False, server_default="draft", index=True
    )
    quotation_valid_until = db.Column(db.Date)
    start_date = db.Column(db.Date)
    next_billing_date = db.Column(db.Date)
    expires_on = db.Column(db.Date)
    closed_at = db.Column(db.DateTime(timezone=True))
    notes = db.Column(db.Text)

    customer = db.relationship("Customer")
    plan = db.relationship("Plan")
    template = db.relationship("QuotationTemplate")
    discount = db.relationship("Discount")
    lines = db.relationship(
        "SubscriptionLine", back_populates="subscription", cascade="all, delete-orphan"
    )


class SubscriptionLine(TimestampMixin, db.Model):
    __tablename__ = "subscription_lines"
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["variant_id", "product_id"],
            ["product_variants.id", "product_variants.product_id"],
            ondelete="RESTRICT",
        ),
        db.CheckConstraint("quantity > 0", name="quantity_positive"),
        db.CheckConstraint("unit_price >= 0", name="unit_price_not_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(
        db.Integer,
        db.ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    variant_id = db.Column(db.Integer, index=True)
    tax_id = db.Column(
        db.Integer, db.ForeignKey("taxes.id", ondelete="RESTRICT"), index=True
    )
    quantity = db.Column(db.Integer, nullable=False, server_default="1")
    # Base price plus variant extra, fixed when the line is created.
    unit_price = db.Column(Money, nullable=False)

    subscription = db.relationship("Subscription", back_populates="lines")
    product = db.relationship("Product")
    variant = db.relationship("ProductVariant", overlaps="product")
    tax = db.relationship("Tax")
