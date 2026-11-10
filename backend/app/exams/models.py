"""
Exams, Academic Calendar & Report Cards Data Models — Mind V2
Includes:
- CalendarEvent: School/Band/Class events, blackout periods, and exam periods
- ExamBlueprint: Band-wide exam specifications and Multi-Set (A-D) metadata
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.db import Base
from backend.app.tenancy.models import UUIDBase, TenantMixin


class CalendarEventType:
    BLACKOUT = "blackout"
    EXAM_PERIOD = "exam_period"
    HOLIDAY = "holiday"
    EVENT = "event"
    ASSESSMENT = "assessment"


class CalendarEvent(UUIDBase, TenantMixin):
    __tablename__ = "calendar_events"
    __table_args__ = (
        Index("ix_calendar_school_dates", "school_id", "starts_at", "ends_at"),
        Index("ix_calendar_scope", "school_id", "band_id", "class_id", "section_id"),
    )

    academic_year_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True
    )
    band_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bands.id", ondelete="SET NULL"), nullable=True, index=True
    )
    class_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("classes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), default="event", nullable=False)  # blackout, exam_period, holiday, event
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    creator: Mapped["User"] = relationship("User")  # type: ignore # noqa: F821


class ExamBlueprintStatus:
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"
    PUBLISHED = "published"


class ExamBlueprint(UUIDBase, TenantMixin):
    __tablename__ = "exam_blueprints"
    __table_args__ = (
        Index("ix_blueprints_school_band", "school_id", "band_id"),
        Index("ix_blueprints_status", "status"),
    )

    band_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    academic_year_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True
    )
    creator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    term: Mapped[str] = mapped_column(String(50), default="Term 1", nullable=False)

    # Structure specification: section breakdown, question types, mark counts, difficulty ratios, topic list
    structure_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Generated sets: Set A, Set B, Set C, Set D metadata and item references
    sets_data_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    status: Mapped[str] = mapped_column(String(30), default=ExamBlueprintStatus.DRAFT, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id])  # type: ignore # noqa: F821
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])  # type: ignore # noqa: F821

