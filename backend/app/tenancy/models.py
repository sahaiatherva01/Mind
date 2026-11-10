"""
Tenancy Models: School and AcademicYear
"""
from datetime import date
from typing import List, Optional
from sqlalchemy import String, Date, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.db import UUIDBase, TenantMixin


class School(UUIDBase):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    board: Mapped[Optional[str]] = mapped_column(String(50), default="ICSE/ISC", nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, suspended, archived
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    academic_years: Mapped[List["AcademicYear"]] = relationship(
        "AcademicYear", back_populates="school", cascade="all, delete-orphan"
    )
    bands: Mapped[List["Band"]] = relationship(
        "Band", back_populates="school", cascade="all, delete-orphan"
    )
    users: Mapped[List["User"]] = relationship(  # type: ignore # noqa: F821
        "User", back_populates="school", cascade="all, delete-orphan"
    )


class Band(UUIDBase, TenantMixin):
    """
    Academic Band per school (e.g., Classes 6–8, 9–10, 11–12).
    Coordinators are scoped to exactly one band.
    """
    __tablename__ = "bands"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_school_band_name"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Secondary (9-10)"
    min_grade: Mapped[int] = mapped_column(nullable=False)
    max_grade: Mapped[int] = mapped_column(nullable=False)

    school: Mapped["School"] = relationship("School", back_populates="bands")
    classes: Mapped[List["Class"]] = relationship(  # type: ignore # noqa: F821
        "Class", back_populates="band"
    )



class AcademicYear(UUIDBase, TenantMixin):
    __tablename__ = "academic_years"
    __table_args__ = (
        UniqueConstraint("school_id", "label", name="uq_school_academic_year_label"),
    )

    label: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "2026-2027"
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, archived, upcoming

    school: Mapped["School"] = relationship("School", back_populates="academic_years")
    classes: Mapped[List["Class"]] = relationship(  # type: ignore # noqa: F821
        "Class", back_populates="academic_year", cascade="all, delete-orphan"
    )

