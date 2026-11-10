"""
Identity Authorization Policies — Mind V2
"""
from backend.app.identity.models import User, RoleName
from backend.app.core.errors import ForbiddenException


def can_manage_users(current_user: User) -> bool:
    roles = {r.role for r in current_user.role_assignments if r.status == "active"}
    if RoleName.PLATFORM_ADMIN in roles or RoleName.SCHOOL_ADMIN in roles or RoleName.ACADEMIC_COORDINATOR in roles:
        return True
    raise ForbiddenException("Only school administrators or coordinators can manage user accounts")
