from sqlalchemy.orm import Session

from app.db.models import AuditLog

SENSITIVE_PARTS = ("key", "secret", "token", "password")


def sanitize_details(value):
    if isinstance(value, dict):
        return {
            key: ("[filtered]" if any(part in key.lower() for part in SENSITIVE_PARTS) else sanitize_details(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_details(item) for item in value]
    return value


def record_audit(
    db: Session,
    actor_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict | None = None,
) -> AuditLog:
    event = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=sanitize_details(details or {}),
    )
    db.add(event)
    return event
