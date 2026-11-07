"""
Audit Policies: Only School Administrators can view audit events.
"""
from backend.app.core.errors import ForbiddenException
from backend.app.identity.models import User


def can_view_audit_logs(user: User) -> bool:
    if user.role != "admin":
        raise ForbiddenException("Only school administrators can access audit event logs")
    return True
