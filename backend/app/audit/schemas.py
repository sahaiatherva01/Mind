"""
Audit Schemas
"""
from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: str
    school_id: str
    actor_id: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditEventListResponse(BaseModel):
    items: List[AuditEventResponse]
    total: int
