"""
Pydantic Schemas for Notifications
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class NotificationOut(BaseModel):
    id: str
    school_id: str
    user_id: str
    title: str
    message: str
    type: str
    channel: str
    link_url: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    delivery_status: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None


class NotificationCreate(BaseModel):
    user_id: str
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=1000)
    type: str = "system"
    channel: str = "in_app"
    link_url: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class NotificationBulkCreate(BaseModel):
    user_ids: List[str]
    title: str
    message: str
    type: str = "system"
    channel: str = "in_app"
    link_url: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class UnreadCountResponse(BaseModel):
    unread_count: int
