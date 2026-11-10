"""
Identity Models: User, RoleAssignment, Session, PasswordResetToken
Enforces the 5 canonical roles:
- platform_admin (global)
- school_admin (school-scoped)
- academic_coordinator (school + band-scoped)
- teacher (school + class/section/subject-scoped)
- student (school + enrollment-scoped)
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.db import UUIDBase


class RoleName:
    PLATFORM_ADMIN = "platform_admin"
    SCHOOL_ADMIN = "school_admin"
    ACADEMIC_COORDINATOR = "academic_coordinator"
    TEACHER = "teacher"
    STUDENT = "student"

    ALL_ROLES = [PLATFORM_ADMIN, SCHOOL_ADMIN, ACADEMIC_COORDINATOR, TEACHER, STUDENT]


# Legacy alias for backward compatibility during phased refactor
class UserRole:
    ADMIN = RoleName.SCHOOL_ADMIN
    PLATFORM_ADMIN = RoleName.PLATFORM_ADMIN
    SCHOOL_ADMIN = RoleName.SCHOOL_ADMIN
    ACADEMIC_COORDINATOR = RoleName.ACADEMIC_COORDINATOR
    TEACHER = RoleName.TEACHER
    STUDENT = RoleName.STUDENT


class User(UUIDBase):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("school_id", "email", name="uq_school_user_email"),
        Index("ix_users_email", "email"),
        Index("ix_users_school", "school_id"),
    )

    # school_id is nullable strictly for Platform Admins (who control cross-school)
    school_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # 'active', 'inactive', 'suspended'
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    school: Mapped[Optional["School"]] = relationship("School", back_populates="users")  # type: ignore # noqa: F821
    role_assignments: Mapped[List["RoleAssignment"]] = relationship(
        "RoleAssignment", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def primary_role(self) -> str:
        """Determines effective highest role for navigation and display."""
        active_assignments = [r for r in self.role_assignments if r.status == "active"]
        roles = {r.role for r in active_assignments}
        if RoleName.PLATFORM_ADMIN in roles:
            return RoleName.PLATFORM_ADMIN
        if RoleName.SCHOOL_ADMIN in roles:
            return RoleName.SCHOOL_ADMIN
        if RoleName.ACADEMIC_COORDINATOR in roles:
            return RoleName.ACADEMIC_COORDINATOR
        if RoleName.TEACHER in roles:
            return RoleName.TEACHER
        if RoleName.STUDENT in roles:
            return RoleName.STUDENT
        return RoleName.STUDENT

    @property
    def role(self) -> str:
        """Backward-compatible role string for legacy references."""
        return self.primary_role


class RoleAssignment(UUIDBase):
    """
    Scoped RBAC assignment: binds a user to a role, tenant (school),
    and optional scope parameters (band for academic coordinator).
    """
    __tablename__ = "role_assignments"
    __table_args__ = (
        Index("ix_role_assignments_user_active", "user_id", "status"),
        Index("ix_role_assignments_lookup", "school_id", "role", "status"),
        Index("ix_role_assignments_band", "band_id"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    # school_id is nullable only for platform_admin
    school_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # band_id is set specifically for academic_coordinator
    band_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bands.id", ondelete="SET NULL"), nullable=True, index=True
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # 'active', 'revoked'

    user: Mapped["User"] = relationship("User", back_populates="role_assignments")
    school: Mapped[Optional["School"]] = relationship("School")  # type: ignore # noqa: F821
    band: Mapped[Optional["Band"]] = relationship("Band")  # type: ignore # noqa: F821


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
