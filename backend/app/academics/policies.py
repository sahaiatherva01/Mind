"""
Academics Authorization Policies — Mind V2
"""
from backend.app.core.errors import ForbiddenException
from backend.app.identity.models import User, RoleName


def can_manage_academic_setup(user: User) -> bool:
    roles = {r.role for r in user.role_assignments if r.status == "active"}
    if RoleName.PLATFORM_ADMIN in roles or RoleName.SCHOOL_ADMIN in roles:
        return True
    raise ForbiddenException("Only school administrators can modify academic structures and assignments")


def can_view_academics(user: User) -> bool:
    return True
