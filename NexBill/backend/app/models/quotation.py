"""Quotation templates, the starting point for new subscriptions."""
from app.extensions import db
from app.models.base import TimestampMixin


class QuotationTemplate(TimestampMixin, db.Model):
    __tablename__ = "quotation_templates"
    __table_args__ = (
        db.CheckConstraint("validity_days > 0", name="validity_days_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    validity_days = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())

    plan = db.relationship("Plan")
    lines = db.relationship(
        "TemplateLine", back_populates="template", cascade="all, delete-orphan"
    )


class TemplateLine(TimestampMixin, db.Model):
    __tablename__ = "template_lines"
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["variant_id", "product_id"],
            ["product_variants.id", "product_variants.product_id"],
            ondelete="RESTRICT",
        ),
        db.CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer,
        db.ForeignKey("quotation_templates.id", ondelete="CASCADE"),
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

    template = db.relationship("QuotationTemplate", back_populates="lines")
    product = db.relationship("Product")
    variant = db.relationship("ProductVariant", overlaps="product")
    tax = db.relationship("Tax")
