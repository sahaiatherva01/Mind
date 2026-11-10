"""
Advanced Academic Workflows Models — Mind V2 (Phase 8)
Includes:
- CoordinatorIntervention: Early-warning at-risk tracking & pedagogical interventions
- SmartStudentGroup: Dynamic student segmentation based on concept mastery
- StudentAcademicGoal: Personalized target setting & progress tracking
- StudentDoubtQuery: Structured student academic doubt routing to assigned teachers
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


class CoordinatorIntervention(UUIDBase, TenantMixin):
    __tablename__ = "coordinator_interventions"
    __table_args__ = (
        Index("ix_interventions_school_band", "school_id", "band_id"),
        Index("ix_interventions_student", "student_id"),
        Index("ix_interventions_status", "status"),
    )

    band_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    trigger_reason: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)  # open, in_progress, resolved
    action_taken: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])  # type: ignore # noqa: F821
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])  # type: ignore # noqa: F821


class SmartStudentGroup(UUIDBase, TenantMixin):
    __tablename__ = "smart_student_groups"
    __table_args__ = (
        Index("ix_smart_groups_scope", "school_id", "class_id", "section_id", "subject_id"),
    )

    class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_type: Mapped[str] = mapped_column(String(50), default="remedial", nullable=False)  # remedial, core, advanced
    criteria_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    student_ids_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    weak_topics_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class StudentAcademicGoal(UUIDBase, TenantMixin):
    __tablename__ = "student_academic_goals"
    __table_args__ = (
        Index("ix_student_goals", "school_id", "student_id", "subject_id"),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    target_score_pct: Mapped[float] = mapped_column(Float, nullable=False)
    current_score_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="in_progress", nullable=False)  # in_progress, achieved, missed
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class StudentDoubtQuery(UUIDBase, TenantMixin):
    __tablename__ = "student_doubt_queries"
    __table_args__ = (
        Index("ix_doubt_queries_student", "school_id", "student_id"),
        Index("ix_doubt_queries_teacher", "school_id", "teacher_id", "status"),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, answered
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])  # type: ignore # noqa: F821
    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id])  # type: ignore # noqa: F821

