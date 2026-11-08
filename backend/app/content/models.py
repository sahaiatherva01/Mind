"""
Content Models: Question Bank and Source Assets
"""
from typing import Optional, List
from sqlalchemy import String, Integer, JSON, ForeignKey, Index
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

