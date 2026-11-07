"""
Tenancy Authorization Policies
"""
from backend.app.core.errors import ForbiddenException, TenantMismatchException
from backend.app.identity.models import User


def can_manage_tenancy(user: User, school_id: str) -> bool:
    if user.school_id != school_id:
        raise TenantMismatchException("Cannot access or configure another school's tenancy")
    if user.role != "admin":
        raise ForbiddenException("Only school administrators can manage academic years and settings")
    return True
