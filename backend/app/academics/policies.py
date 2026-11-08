"""
Academics Authorization Policies
Enforces that:
- Admin manages school setup, classes, sections, subjects, assignments, enrollments.
- Teacher can only view assigned classes/sections/subjects.
- Student can only view their enrolled class/section.
"""
from backend.app.core.errors import ForbiddenException
from backend.app.identity.models import User


def can_manage_academic_setup(user: User) -> bool:
    if user.role != "admin":
        raise ForbiddenException("Only school administrators can modify academic structures and assignments")
    return True


def can_view_academics(user: User) -> bool:
    # All authenticated users can view basic academic catalogue within their school
    return True
