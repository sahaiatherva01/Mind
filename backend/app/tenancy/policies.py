"""
Tenancy Authorization Policies — Mind V2
"""
from backend.app.core.errors import ForbiddenException, TenantMismatchException
from backend.app.identity.models import User, RoleName


def can_manage_tenancy(user: User, school_id: str) -> bool:
    roles = {r.role for r in user.role_assignments if r.status == "active"}
    if RoleName.PLATFORM_ADMIN in roles:
        return True
    if user.school_id != school_id:
        raise TenantMismatchException("Cannot access or configure another school's tenancy")
    if RoleName.SCHOOL_ADMIN not in roles:
        raise ForbiddenException("Only school administrators can manage academic years, bands, and settings")
    return True
