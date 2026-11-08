"""
Assessment Models
Assessment State Machine:
draft → needs_review → approved → scheduled | published → closed → evaluated → results_released
"""
from typing import List, Optional
from sqlalchemy import String, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.db import UUIDBase, TenantMixin


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
