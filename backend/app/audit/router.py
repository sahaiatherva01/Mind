"""
Audit Router: GET /audit-events
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.audit import service, policies
from backend.app.audit.schemas import AuditEventListResponse, AuditEventResponse

router = APIRouter(prefix="/audit-events", tags=["Audit"])


@router.get("", response_model=AuditEventListResponse)
async def list_audit_events(
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_view_audit_logs(current_user)
    events = await service.get_audit_events(
        db=db,
        school_id=current_user.school_id,
        limit=limit,
        entity_type=entity_type,
        action=action,
    )
    return AuditEventListResponse(
        items=[AuditEventResponse.model_validate(e) for e in events],
        total=len(events),
    )
