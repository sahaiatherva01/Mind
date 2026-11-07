"""
Audit Event Service
Records auditable system events (logins, user creations, assignments, publishing).
"""
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.audit.models import AuditEvent


async def record_audit_event(
    db: AsyncSession,
    school_id: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    event = AuditEvent(
        school_id=school_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata_json or {},
    )
    db.add(event)
    await db.flush()
    return event


async def get_audit_events(
    db: AsyncSession,
    school_id: str,
    limit: int = 50,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
) -> List[AuditEvent]:
    stmt = select(AuditEvent).where(AuditEvent.school_id == school_id)
    if entity_type:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditEvent.action == action)

    stmt = stmt.order_by(desc(AuditEvent.created_at)).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
