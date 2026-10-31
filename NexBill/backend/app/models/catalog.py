"""Catalog: products, variants, taxes, plans and discounts."""
from app.extensions import db
from app.models.base import Money, Percentage, TimestampMixin, enum_check
from app.models.enums import BillingPeriod, DiscountScope, DiscountType, ProductType

discount_products = db.Table(
    "discount_products",
    db.Column(
        "discount_id",
        db.Integer,
        db.ForeignKey("discounts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "product_id",
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Product(TimestampMixin, db.Model):
    __tablename__ = "products"
    __table_args__ = (
        enum_check("product_type", ProductType),
        db.CheckConstraint("sales_price >= 0", name="sales_price_not_negative"),
        db.CheckConstraint("cost_price >= 0", name="cost_price_not_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text)
    product_type = db.Column(db.String(20), nullable=False, server_default="service")
    sales_price = db.Column(Money, nullable=False)
    cost_price = db.Column(Money, nullable=False, server_default="0")
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())

    variants = db.relationship(
        "ProductVariant", back_populates="product", cascade="all, delete-orphan"
    )


class ProductVariant(TimestampMixin, db.Model):
    """An attribute value with an extra price, e.g. Brand = Odoo, +560."""

    __tablename__ = "product_variants"
    __table_args__ = (
        db.UniqueConstraint(
            "product_id", "attribute", "value", name="uq_product_variants_attribute_value"
        ),
        # Target of the composite foreign keys on template and subscription lines,
        # which guarantee that a line's variant belongs to the line's product.
        db.UniqueConstraint("id", "product_id", name="uq_product_variants_id_product_id"),
        db.CheckConstraint("extra_price >= 0", name="extra_price_not_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    extra_price = db.Column(Money, nullable=False, server_default="0")
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())

    product = db.relationship("Product", back_populates="variants")


class Tax(TimestampMixin, db.Model):
    __tablename__ = "taxes"
    __table_args__ = (
        db.CheckConstraint("rate >= 0 AND rate <= 100", name="rate_between_0_and_100"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    rate = db.Column(Percentage, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())


class Plan(TimestampMixin, db.Model):
    __tablename__ = "plans"
    __table_args__ = (
        enum_check("billing_period", BillingPeriod),
        db.CheckConstraint("price >= 0", name="price_not_negative"),
        db.CheckConstraint("billing_interval > 0", name="billing_interval_positive"),
        db.CheckConstraint("min_quantity > 0", name="min_quantity_positive"),
        db.CheckConstraint("valid_to >= valid_from", name="valid_to_not_before_valid_from"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    price = db.Column(Money, nullable=False, server_default="0")
    billing_period = db.Column(db.String(20), nullable=False)
    billing_interval = db.Column(db.Integer, nullable=False, server_default="1")
    min_quantity = db.Column(db.Integer, nullable=False, server_default="1")
    valid_from = db.Column(db.Date)
    valid_to = db.Column(db.Date)
    is_auto_close = db.Column(db.Boolean, nullable=False, server_default=db.false())
    is_closable = db.Column(db.Boolean, nullable=False, server_default=db.true())
    is_pausable = db.Column(db.Boolean, nullable=False, server_default=db.false())
    is_renewable = db.Column(db.Boolean, nullable=False, server_default=db.false())
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())


class Discount(TimestampMixin, db.Model):
    __tablename__ = "discounts"
    __table_args__ = (
        enum_check("discount_type", DiscountType),
        enum_check("scope", DiscountScope),
        db.CheckConstraint("value > 0", name="value_positive"),
        db.CheckConstraint(
            "discount_type <> 'percent' OR value <= 100", name="percent_at_most_100"
        ),
        db.CheckConstraint("min_purchase >= 0", name="min_purchase_not_negative"),
        db.CheckConstraint("min_quantity > 0", name="min_quantity_positive"),
        db.CheckConstraint("valid_to >= valid_from", name="valid_to_not_before_valid_from"),
        db.CheckConstraint("usage_count >= 0", name="usage_count_not_negative"),
        db.CheckConstraint("usage_count <= usage_limit", name="usage_count_within_limit"),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)
    scope = db.Column(db.String(20), nullable=False, server_default="subscription")
    value = db.Column(Money, nullable=False)
    min_purchase = db.Column(Money, nullable=False, server_default="0")
    min_quantity = db.Column(db.Integer, nullable=False, server_default="1")
    valid_from = db.Column(db.Date)
    valid_to = db.Column(db.Date)
    # An empty usage_limit means unlimited.
    usage_limit = db.Column(db.Integer)
    usage_count = db.Column(db.Integer, nullable=False, server_default="0")
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())

    products = db.relationship("Product", secondary=discount_products)
