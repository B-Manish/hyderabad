"""Audit logging service — writes to audit_logs table."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    entity_type: str,
    entity_id: uuid.UUID | None,
    action: str,
    metadata_json: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        id=uuid.uuid4(),
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        metadata_json=metadata_json,
    )
    db.add(log)
    await db.flush()
    return log
