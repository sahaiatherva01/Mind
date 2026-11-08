"""
Generation Job Models
State machine: queued → running → succeeded | failed | cancelled
"""
from typing import Optional
from sqlalchemy import String, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.db import UUIDBase, TenantMixin


class GenerationJob(UUIDBase, TenantMixin):
    __tablename__ = "generation_jobs"
    __table_args__ = (
        Index("ix_generation_jobs_school_status", "school_id", "status"),
        Index("ix_generation_jobs_requester", "requester_id"),
    )

    requester_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)  # queued, running, succeeded, failed, cancelled
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)

    input_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    warnings: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

