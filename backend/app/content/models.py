"""
Content Models: Question Bank, Source Assets, Learning Materials & Distribution
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.db import UUIDBase, TenantMixin


class Question(UUIDBase, TenantMixin):
    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_school_subject", "school_id", "subject_id"),
        Index("ix_questions_type_difficulty", "type", "difficulty"),
    )

    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # objective, written, visual_mathematical, etc.
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 40 question types
    prompt: Mapped[str] = mapped_column(String(2000), nullable=False)
    marks: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    topic_tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Structured question content & answers
    content_data: Mapped[dict] = mapped_column(JSON, default=dict)
    answer_data: Mapped[dict] = mapped_column(JSON, default=dict)  # Teacher only until release

    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ContentAsset(UUIDBase, TenantMixin):
    __tablename__ = "content_assets"

    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)


class Material(UUIDBase, TenantMixin):
    __tablename__ = "materials"
    __table_args__ = (
        Index("ix_materials_school_subject", "school_id", "subject_id"),
        Index("ix_materials_school_class", "school_id", "class_id"),
    )

    uploader_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), default="application/pdf", nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chapter: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    distributions: Mapped[List["MaterialDistribution"]] = relationship(
        "MaterialDistribution", back_populates="material", cascade="all, delete-orphan", lazy="selectin"
    )
    engagements: Mapped[List["MaterialEngagement"]] = relationship(
        "MaterialEngagement", back_populates="material", cascade="all, delete-orphan", lazy="selectin"
    )


class MaterialDistribution(UUIDBase, TenantMixin):
    __tablename__ = "material_distributions"
    __table_args__ = (
        Index("ix_material_dist_mat_sec", "material_id", "section_id", unique=True),
    )

    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    distributed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    distributed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="distributions")


class MaterialEngagement(UUIDBase, TenantMixin):
    __tablename__ = "material_engagements"
    __table_args__ = (
        Index("ix_mat_engagement_mat_student", "material_id", "student_id"),
    )

    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sections.id"), nullable=True, index=True)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_read: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="engagements")


class QuestionExtractionJob(UUIDBase, TenantMixin):
    __tablename__ = "question_extraction_jobs"

    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requester_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)  # queued, running, succeeded, failed
    extracted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    results_json: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
