"""
Audit Trail Model
Maintains an immutable record of security and administrative events.
"""
from typing import Optional
from sqlalchemy import String, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.db import UUIDBase, TenantMixin


class AuditEvent(UUIDBase, TenantMixin):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_school_action", "school_id", "action"),
        Index("ix_audit_school_entity", "school_id", "entity_type", "entity_id"),
        Index("ix_audit_actor", "actor_id"),
    )

    actor_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # None if system/anonymous
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'user.login', 'assessment.publish'
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user', 'assessment', 'class'
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
