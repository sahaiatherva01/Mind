"""
Academic Models: Class, Section, Subject, TeacherAssignment, StudentEnrollment, CurriculumNode
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, ForeignKey, Index, UniqueConstraint, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.db import UUIDBase, TenantMixin


class Class(UUIDBase, TenantMixin):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("school_id", "academic_year_id", "name", name="uq_school_year_class_name"),
    )

    academic_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True
    )
    band_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bands.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Class 11", "Class 12"
    grade_level: Mapped[Optional[int]] = mapped_column(nullable=True)  # e.g., 11, 12

    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="classes")  # type: ignore # noqa: F821
    band: Mapped[Optional["Band"]] = relationship("Band", back_populates="classes")  # type: ignore # noqa: F821
    sections: Mapped[List["Section"]] = relationship("Section", back_populates="class_obj", cascade="all, delete-orphan")



class Section(UUIDBase):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("class_id", "name", name="uq_class_section_name"),
    )

    class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "A", "E", "D"
    roster_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, verified, locked

    class_obj: Mapped["Class"] = relationship("Class", back_populates="sections")


class Subject(UUIDBase, TenantMixin):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_school_subject_code"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., "Physics"
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # e.g., "PHY"


class TeacherAssignment(UUIDBase, TenantMixin):
    __tablename__ = "teacher_assignments"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "teacher_id", "class_id", "section_id", "subject_id",
            name="uq_teacher_class_section_subject"
        ),
        Index("ix_teacher_assignments_lookup", "school_id", "teacher_id"),
        Index("ix_teacher_scope", "teacher_id", "class_id", "section_id", "subject_id"),
    )

    teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
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
    academic_year_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_class_teacher: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_substitute: Mapped[bool] = mapped_column(default=False, nullable=False)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, inactive

    teacher: Mapped["User"] = relationship("User")  # type: ignore # noqa: F821
    class_obj: Mapped["Class"] = relationship("Class")
    section: Mapped["Section"] = relationship("Section")
    subject: Mapped["Subject"] = relationship("Subject")


class StudentEnrollment(UUIDBase, TenantMixin):
    __tablename__ = "student_enrollments"
    __table_args__ = (
        UniqueConstraint("school_id", "student_id", "class_id", "section_id", name="uq_student_enrollment"),
        Index("ix_student_enrollment_lookup", "school_id", "student_id"),
        Index("ix_student_enrollment_roll", "school_id", "section_id", "roll_number"),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    academic_year_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=True, index=True
    )
    class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    roll_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # 'active', 'withdrawn'

    student: Mapped["User"] = relationship("User")  # type: ignore # noqa: F821
    class_obj: Mapped["Class"] = relationship("Class")
    section: Mapped["Section"] = relationship("Section")



class CurriculumNode(UUIDBase, TenantMixin):
    __tablename__ = "curriculum_nodes"
    __table_args__ = (
        Index("ix_curriculum_lookup", "school_id", "subject_id", "grade"),
        Index("ix_curriculum_chapter_topic", "subject_id", "chapter", "topic"),
    )

    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    grade: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "11", "12", "10"
    board: Mapped[str] = mapped_column(String(20), default="ICSE/ISC", nullable=False)  # ICSE, ISC, etc.
    chapter: Mapped[str] = mapped_column(String(200), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    learning_outcome: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject")


class RosterChangeRequest(UUIDBase, TenantMixin):
    __tablename__ = "roster_change_requests"
    __table_args__ = (
        Index("ix_roster_requests_lookup", "school_id", "section_id", "status"),
    )

    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # add_student, remove_student, update_roll
    student_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    reviewed_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    section: Mapped["Section"] = relationship("Section")
    requested_by: Mapped["User"] = relationship("User", foreign_keys=[requested_by_id])

