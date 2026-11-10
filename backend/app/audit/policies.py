"""
Audit Policies — Mind V2
Only Platform Admins and School Administrators can view audit events.
"""
from backend.app.core.errors import ForbiddenException
from backend.app.identity.models import User, RoleName


def can_view_audit_logs(user: User) -> bool:
    roles = {r.role for r in user.role_assignments if r.status == "active"}
    if RoleName.PLATFORM_ADMIN in roles or RoleName.SCHOOL_ADMIN in roles or user.role in ("admin", "school_admin"):
        return True
    raise ForbiddenException("Only school or platform administrators can access audit event logs")
