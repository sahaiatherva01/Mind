"""
The Permission Engine: Single Authorization Policy Layer
Enforces:
1. Deny by default.
2. Cross-school access strictly denied (Tenant boundary).
3. Admin = School administration actions within their school.
4. Teacher = Explicit TeacherAssignment(class, section, subject) only.
5. Student = Active StudentEnrollment within their assigned class/section.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import ForbiddenException, TenantMismatchException
from backend.app.identity.models import User
from backend.app.academics.models import TeacherAssignment, StudentEnrollment


def verify_tenant_boundary(user: User, resource_school_id: str) -> None:
    """Verifies that the user and the requested resource belong to the exact same school."""
    if user.school_id != resource_school_id:
        raise TenantMismatchException("Cross-tenant access strictly denied")


def can_admin_school(user: User, school_id: str) -> bool:
    """Checks whether the user is an active Admin for the given school."""
    if user.role != "admin" or user.school_id != school_id:
        raise ForbiddenException("Action requires school administrator privileges")
    return True


async def can_teacher_access_class(
    db: AsyncSession,
    user: User,
    class_id: str,
    section_id: str,
    subject_id: Optional[str] = None
) -> bool:
    """
    Verifies that a teacher has an explicit assignment for the class, section, and optional subject.
    Admins are also permitted to view academic structures.
    """
    if user.role == "admin":
        return True

    if user.role != "teacher":
        raise ForbiddenException("Only teachers or school administrators can access this workspace")

    stmt = select(TeacherAssignment).where(
        TeacherAssignment.school_id == user.school_id,
        TeacherAssignment.teacher_id == user.id,
        TeacherAssignment.class_id == class_id,
        TeacherAssignment.section_id == section_id
    )
    if subject_id:
        stmt = stmt.where(TeacherAssignment.subject_id == subject_id)

    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise ForbiddenException(
            "Access denied: You are not assigned to this class, section, and subject combination"
        )
    return True


async def can_student_access_class(
    db: AsyncSession,
    user: User,
    class_id: str,
    section_id: str
) -> bool:
    """Verifies that a student is actively enrolled in the class and section."""
    if user.role != "student":
        return False

    stmt = select(StudentEnrollment).where(
        StudentEnrollment.school_id == user.school_id,
        StudentEnrollment.student_id == user.id,
        StudentEnrollment.class_id == class_id,
        StudentEnrollment.section_id == section_id,
        StudentEnrollment.status == "active"
    )
    result = await db.execute(stmt)
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise ForbiddenException("Student is not enrolled in this class and section")
    return True

