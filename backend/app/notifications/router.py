"""
Notification API Router
Endpoints:
- GET /notifications: List user notifications
- PATCH /notifications/{id}/read: Mark single notification read
- POST /notifications/mark-all-read: Mark all notifications read
- GET /notifications/unread-count: Get unread count
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.notifications import service
from backend.app.notifications.schemas import NotificationOut, UnreadCountResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationOut])
async def get_my_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists recent notifications for the logged-in user."""
    return await service.list_user_notifications(
        db=db,
        user_id=current_user.id,
        school_id=current_user.school_id,
        unread_only=unread_only,
        limit=limit,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_my_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns number of unread notifications for badge counters."""
    count = await service.get_unread_count(
        db=db,
        user_id=current_user.id,
        school_id=current_user.school_id,
    )
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marks a specific notification as read."""
    return await service.mark_notification_as_read(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id,
    )


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marks all unread notifications for the user as read."""
    count = await service.mark_all_as_read(
        db=db,
        user_id=current_user.id,
        school_id=current_user.school_id,
    )
    return {"marked_count": count}
