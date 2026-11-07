"""
Identity Models: User, Session, PasswordResetToken
Enforces the 3 canonical roles: 'admin', 'teacher', 'student'.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.db import UUIDBase, TenantMixin


class User(UUIDBase, TenantMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("school_id", "email", name="uq_school_user_email"),
        Index("ix_users_school_role", "school_id", "role"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'admin', 'teacher', 'student'
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., 'Academic Coordinator', 'Principal'
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # 'active', 'inactive', 'suspended'

    school: Mapped["School"] = relationship("School", back_populates="users")  # type: ignore # noqa: F821
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )


class Session(UUIDBase):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_token_hash", "token_hash", unique=True),
    )

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class PasswordResetToken(UUIDBase):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_reset_token_hash", "token_hash", unique=True),
    )

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="reset_tokens")
