import json
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.core.logging import logger, mask_sensitive_data
from app.models.audit_log import AuditLog


def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    details: Optional[Any] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Safely record an audit log event ensuring all details are sanitized 
    and no customer PII is persisted in the audit trail.
    """
    sanitized_details = None
    if details is not None:
        if isinstance(details, (dict, list)):
            raw_str = json.dumps(details)
        else:
            raw_str = str(details)
        sanitized_details = mask_sensitive_data(raw_str)

    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=sanitized_details,
        ip_address=ip_address or "127.0.0.1",
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)

    logger.info(f"AUDIT: [{action}] on [{entity_type}:{entity_id}] by User {user_id}")
    return audit_entry
