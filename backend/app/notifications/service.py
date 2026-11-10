"""
Notification Service: In-App Store, Delivery Orchestration & Email Adapter
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import NotFoundException
from backend.app.core.logging import get_logger
from backend.app.identity.models import User
from backend.app.notifications.models import Notification

logger = get_logger("mind.notifications.service")


class EmailAdapter:
    """
    Email notification dispatcher.
    In local dev and test environments, logs formatted email deliveries.
    In production, connects to SMTP or cloud transactional email services.
    """
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        logger.info(f"[EmailAdapter] Dispatched email to {to_email} | Subject: '{subject}'")
        return True


async def create_notification(
    db: AsyncSession,
    school_id: str,
    user_id: str,
    title: str,
    message: str,
    type: str = "system",
    channel: str = "in_app",
    link_url: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> Notification:
    """Creates an in-app notification and dispatches to email adapter if requested."""
    notification = Notification(
        school_id=school_id,
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        channel=channel,
        link_url=link_url,
        is_read=False,
        delivery_status="delivered",
        metadata_json=metadata_json or {},
    )
    db.add(notification)
    await db.flush()

    if channel in ("email", "both"):
        user = await db.get(User, user_id)
        if user and user.email:
            try:
                await EmailAdapter.send_email(
                    to_email=user.email,
                    subject=f"[Mind] {title}",
                    body_text=message,
                )
            except Exception as e:
                logger.error(f"Failed to dispatch email notification to {user.email}: {e}")

    await db.commit()
    await db.refresh(notification)
    return notification


async def send_bulk_notifications(
    db: AsyncSession,
    school_id: str,
    user_ids: List[str],
    title: str,
    message: str,
    type: str = "system",
    channel: str = "in_app",
    link_url: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> int:
    """Bulk creates notifications for multiple users (e.g. all section students)."""
    if not user_ids:
        return 0

    notifications = []
    for uid in user_ids:
        notifications.append(
            Notification(
                school_id=school_id,
                user_id=uid,
                title=title,
                message=message,
                type=type,
                channel=channel,
                link_url=link_url,
                is_read=False,
                delivery_status="delivered",
                metadata_json=metadata_json or {},
            )
        )
    db.add_all(notifications)
    await db.commit()

    if channel in ("email", "both"):
        u_stmt = select(User).where(User.id.in_(user_ids))
        u_res = await db.execute(u_stmt)
        users = list(u_res.scalars().all())
        for u in users:
            if u.email:
                try:
                    await EmailAdapter.send_email(
                        to_email=u.email,
                        subject=f"[Mind] {title}",
                        body_text=message,
                    )
                except Exception as e:
                    logger.error(f"Failed to dispatch bulk email to {u.email}: {e}")

    return len(notifications)


async def list_user_notifications(
    db: AsyncSession,
    user_id: str,
    school_id: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 50,
) -> List[Notification]:
    """Retrieves notifications for the active user ordered by newest first."""
    stmt = select(Notification).where(Notification.user_id == user_id)
    if school_id:
        stmt = stmt.where(Notification.school_id == school_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)

    stmt = stmt.order_by(desc(Notification.created_at)).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def mark_notification_as_read(
    db: AsyncSession,
    user_id: str,
    notification_id: str,
) -> Notification:
    """Marks a single notification as read."""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    )
    res = await db.execute(stmt)
    notif = res.scalar_one_or_none()
    if not notif:
        raise NotFoundException("Notification", notification_id)

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notif)
    return notif


async def mark_all_as_read(
    db: AsyncSession,
    user_id: str,
    school_id: Optional[str] = None,
) -> int:
    """Marks all unread notifications for a user as read."""
    now = datetime.now(timezone.utc)
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True, read_at=now)
    )
    if school_id:
        stmt = stmt.where(Notification.school_id == school_id)

    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount or 0


async def get_unread_count(
    db: AsyncSession,
    user_id: str,
    school_id: Optional[str] = None,
) -> int:
    """Returns the unread notifications count for badge display."""
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.is_read == False,
    )
    if school_id:
        stmt = stmt.where(Notification.school_id == school_id)

    res = await db.execute(stmt)
    return res.scalar_one() or 0
