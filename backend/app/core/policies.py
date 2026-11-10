"""
The Permission Engine: Single Central Authorization Policy Layer — Mind V2
Evaluates role and scope together via:
    authorize(actor, action, resource, db) -> bool | raises ForbiddenException / TenantMismatchException
"""
from typing import Optional, Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import ForbiddenException, TenantMismatchException
from backend.app.identity.models import User, RoleName, RoleAssignment
from backend.app.academics.models import TeacherAssignment, StudentEnrollment, Class
from backend.app.core.permission_matrix import (
    Action,
    PERMISSION_MATRIX,
    get_required_scope,
    is_action_permitted_for_role,
)


def _extract_attr(resource: Any, key: str, default: Any = None) -> Any:
    """Helper to extract a property whether resource is a dict or an object."""
    if resource is None:
        return default
    if isinstance(resource, dict):
        return resource.get(key, default)
    return getattr(resource, key, default)


def verify_tenant_boundary(user: User, resource_school_id: Optional[str]) -> None:
    """Verifies that the user and the requested resource belong to the exact same school."""
    if not resource_school_id:
        return
    # Platform admins have no school and can access cross-tenant
    if user.primary_role == RoleName.PLATFORM_ADMIN:
        return
    if user.school_id != resource_school_id:
        raise TenantMismatchException("Cross-tenant access strictly denied")


async def authorize(
    actor: User,
    action: str,
    resource: Optional[Any] = None,
    db: Optional[AsyncSession] = None
) -> bool:
    """
    Central authorization entry point.
    Evaluates role and scope together. Raises ForbiddenException on denial.
    """
    if not actor or actor.status != "active":
        raise ForbiddenException("User account is inactive or unauthenticated")

    action_rules = PERMISSION_MATRIX.get(action)
    if not action_rules:
        raise ForbiddenException(f"Unknown or unconfigured system action '{action}'")

    active_assignments = []
    if hasattr(actor, "_cached_role_assignments") and actor._cached_role_assignments:
        active_assignments = [r for r in actor._cached_role_assignments if getattr(r, "status", None) == "active"]
    elif "role_assignments" in actor.__dict__ and actor.__dict__["role_assignments"] is not None:
        active_assignments = [r for r in actor.__dict__["role_assignments"] if getattr(r, "status", None) == "active"]
    elif db:
        res = await db.execute(
            select(RoleAssignment).where(RoleAssignment.user_id == actor.id, RoleAssignment.status == "active")
        )
        active_assignments = list(res.scalars().all())

    if not active_assignments:
        raise ForbiddenException("User has no active role assignments")


    # Extract resource scope identifiers
    res_school_id = _extract_attr(resource, "school_id") or actor.school_id
    res_band_id = _extract_attr(resource, "band_id")
    res_class_id = _extract_attr(resource, "class_id")
    res_section_id = _extract_attr(resource, "section_id")
    res_subject_id = _extract_attr(resource, "subject_id")
    res_user_id = _extract_attr(resource, "user_id") or _extract_attr(resource, "student_id")

    # Evaluate each active role assignment held by the actor
    for assignment in active_assignments:
        role = assignment.role
        if role not in action_rules:
            continue

        scope_type = action_rules[role]

        # 1. Global Scope (Platform Admin)
        if scope_type == "global":
            if role == RoleName.PLATFORM_ADMIN:
                return True

        # 2. School Scope (School Admin)
        elif scope_type == "school":
            # Platform Admin always passes school scope
            if role == RoleName.PLATFORM_ADMIN:
                return True
            if assignment.school_id and res_school_id and assignment.school_id == res_school_id:
                return True

        # 3. Band Scope (Academic Coordinator)
        elif scope_type == "band":
            # School admin / Platform admin override within same school
            if role == RoleName.PLATFORM_ADMIN:
                return True
            if role == RoleName.SCHOOL_ADMIN and assignment.school_id == res_school_id:
                return True
            if role == RoleName.ACADEMIC_COORDINATOR:
                if assignment.school_id != res_school_id:
                    continue
                # If resource specifies band_id directly
                if res_band_id and assignment.band_id == res_band_id:
                    return True
                # If resource specifies class_id, check if class belongs to this band
                if res_class_id and db and assignment.band_id:
                    res_class = await db.get(Class, res_class_id)
                    if res_class and res_class.band_id == assignment.band_id:
                        return True
                # If neither band_id nor class_id specified (e.g. band dashboard view)
                if not res_band_id and not res_class_id:
                    return True

        # 4. Assigned Class Scope (Teacher)
        elif scope_type == "assigned_class":
            # School admin / Coordinator can view within their jurisdiction
            if role == RoleName.PLATFORM_ADMIN:
                return True
            if role == RoleName.SCHOOL_ADMIN and assignment.school_id == res_school_id:
                return True
            if role == RoleName.TEACHER and assignment.school_id == res_school_id:
                if not res_class_id or not res_section_id:
                    return True  # General teacher access in school
                if db:
                    stmt = select(TeacherAssignment).where(
                        TeacherAssignment.school_id == assignment.school_id,
                        TeacherAssignment.teacher_id == actor.id,
                        TeacherAssignment.class_id == res_class_id,
                        TeacherAssignment.section_id == res_section_id,
                        TeacherAssignment.status == "active"
                    )
                    if res_subject_id:
                        stmt = stmt.where(TeacherAssignment.subject_id == res_subject_id)
                    res = await db.execute(stmt)
                    if res.scalar_one_or_none():
                        return True
                else:
                    return True

        # 5. Class Teacher Scope (Class Teacher flag or Coordinator of band)
        elif scope_type == "class_teacher":
            if role == RoleName.PLATFORM_ADMIN or role == RoleName.SCHOOL_ADMIN:
                return True
            if role == RoleName.ACADEMIC_COORDINATOR and assignment.school_id == res_school_id:
                if not res_band_id and not res_class_id:
                    return True
                if res_band_id and assignment.band_id == res_band_id:
                    return True
                if res_class_id and db and assignment.band_id:
                    res_class = await db.get(Class, res_class_id)
                    if res_class and res_class.band_id == assignment.band_id:
                        return True
            if role == RoleName.TEACHER and assignment.school_id == res_school_id:
                if not res_class_id or not res_section_id:
                    return True
                if db:
                    stmt = select(TeacherAssignment).where(
                        TeacherAssignment.school_id == assignment.school_id,
                        TeacherAssignment.teacher_id == actor.id,
                        TeacherAssignment.class_id == res_class_id,
                        TeacherAssignment.section_id == res_section_id,
                        TeacherAssignment.is_class_teacher == True,
                        TeacherAssignment.status == "active"
                    )
                    res = await db.execute(stmt)
                    if res.scalar_one_or_none():
                        return True
                else:
                    return True

        # 6. Enrolled Section Scope (Student)
        elif scope_type == "enrolled_section":
            if role == RoleName.STUDENT and assignment.school_id == res_school_id:
                if not res_class_id or not res_section_id:
                    return True
                if db:
                    stmt = select(StudentEnrollment).where(
                        StudentEnrollment.school_id == assignment.school_id,
                        StudentEnrollment.student_id == actor.id,
                        StudentEnrollment.class_id == res_class_id,
                        StudentEnrollment.section_id == res_section_id,
                        StudentEnrollment.status == "active"
                    )
                    res = await db.execute(stmt)
                    if res.scalar_one_or_none():
                        return True
                else:
                    return True

        # 7. Self Scope
        elif scope_type == "self":
            if res_user_id and res_user_id == actor.id:
                return True

    # If loop concludes without granting access
    actor_roles = [r.role for r in active_assignments]
    raise ForbiddenException(
        f"Access denied: Action '{action}' not authorized for roles {actor_roles} within the requested scope"
    )


# Backward-compatible convenience functions that delegate to authorize()
async def can_admin_school(user: User, school_id: str) -> bool:
    return await authorize(user, Action.SCHOOL_PROFILE_UPDATE, {"school_id": school_id})


async def can_teacher_access_class(
    db: AsyncSession,
    user: User,
    class_id: str,
    section_id: str,
    subject_id: Optional[str] = None
) -> bool:
    return await authorize(
        user,
        Action.ASSESSMENT_CREATE,
        {"school_id": user.school_id, "class_id": class_id, "section_id": section_id, "subject_id": subject_id},
        db=db
    )


async def can_student_access_class(
    db: AsyncSession,
    user: User,
    class_id: str,
    section_id: str
) -> bool:
    return await authorize(
        user,
        Action.ASSESSMENT_ATTEMPT,
        {"school_id": user.school_id, "class_id": class_id, "section_id": section_id},
        db=db
    )
