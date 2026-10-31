"""Writes to the audit log. Never pass passwords or tokens in details."""
from app.core.logging import get_request_id
from app.extensions import db
from app.models.audit import AuditLog


def record(
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    actor_user_id: int | None = None,
    details: dict | None = None,
) -> None:
    db.session.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            details=details,
            request_id=get_request_id(),
        )
    )
