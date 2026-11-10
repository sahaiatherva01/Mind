"""
Notifications Data Model — Mind V2
In-app notification store with delivery status, channels, and tenancy scoping.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.db import UUIDBase, TenantMixin


class Notification(UUIDBase, TenantMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_school_created", "school_id", "created_at"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50), default="system", nullable=False
    )  # assignment_published, submission_received, results_released, roster_change, system
    channel: Mapped[str] = mapped_column(
        String(50), default="in_app", nullable=False
    )  # in_app, email, both
    link_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_status: Mapped[str] = mapped_column(
        String(50), default="delivered", nullable=False
    )  # delivered, sent, failed
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore # noqa: F821

