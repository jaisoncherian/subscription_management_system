"""Append-only record of important actions. Never put passwords or tokens in details."""
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    __table_args__ = (
        db.Index("ix_audit_log_entity_type_entity_id", "entity_type", "entity_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    request_id = db.Column(db.String(64))
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        index=True,
    )
