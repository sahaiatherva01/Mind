"""
Assessment Models & Delivery Lifecycle
Assessment State Machine:
draft → needs_review → approved → scheduled | published → closed → evaluated → results_released

Attempt State Machine:
not_started → in_progress → submitted | timed_out
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Boolean, JSON, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.db import UUIDBase, TenantMixin


class AssessmentStatus:
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    CLOSED = "closed"
    EVALUATED = "evaluated"
    RESULTS_RELEASED = "results_released"


class AttemptStatus:
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    TIMED_OUT = "timed_out"


class Assessment(UUIDBase, TenantMixin):
    __tablename__ = "assessments"
    __table_args__ = (
        Index("ix_assessments_school_creator", "school_id", "creator_id"),
        Index("ix_assessments_scope", "class_id", "section_id", "subject_id"),
        Index("ix_assessments_status", "status"),
    )

    creator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id"), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String(36), ForeignKey("sections.id"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # worksheet, quiz, question_paper, custom_question_set
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    total_marks: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    items: Mapped[List["AssessmentItem"]] = relationship(
        "AssessmentItem", back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentItem.position"
    )
    schedule: Mapped[Optional["Schedule"]] = relationship(
        "Schedule", back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    attempts: Mapped[List["Attempt"]] = relationship(
        "Attempt", back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentItem(UUIDBase):
    __tablename__ = "assessment_items"
    __table_args__ = (
        Index("ix_assessment_items_assessment_pos", "assessment_id", "position"),
    )

    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    marks_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="items")
    question: Mapped["Question"] = relationship("Question")  # type: ignore # noqa: F821
    responses: Mapped[List["StudentResponse"]] = relationship(
        "StudentResponse", back_populates="assessment_item", cascade="all, delete-orphan"
    )


class Schedule(UUIDBase):
    __tablename__ = "schedules"

    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Timed exam length
    max_attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Result Release Policy
    result_release_mode: Mapped[str] = mapped_column(
        String(30), default="manual_by_teacher", nullable=False
    )  # manual_by_teacher, immediate_on_submit, scheduled_datetime
    result_release_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="schedule")


class Attempt(UUIDBase, TenantMixin):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("assessment_id", "student_id", "attempt_number", name="uq_attempt_number"),
        Index("ix_attempts_student_status", "student_id", "status"),
        Index("ix_attempts_assessment_status", "assessment_id", "status"),
    )

    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress", nullable=False)  # in_progress, submitted, timed_out

    total_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    is_released: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="attempts")
    student: Mapped["User"] = relationship("User")  # type: ignore # noqa: F821
    responses: Mapped[List["StudentResponse"]] = relationship(
        "StudentResponse", back_populates="attempt", cascade="all, delete-orphan"
    )


class StudentResponse(UUIDBase):
    __tablename__ = "student_responses"
    __table_args__ = (
        UniqueConstraint("attempt_id", "assessment_item_id", name="uq_attempt_item_response"),
    )

    attempt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_items.id", ondelete="CASCADE"), nullable=False, index=True
    )

    answer_json: Mapped[dict] = mapped_column(JSON, default=dict)
    auto_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    manual_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    teacher_feedback: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="responses")
    assessment_item: Mapped["AssessmentItem"] = relationship("AssessmentItem", back_populates="responses")
