"""
Identity Authorization Policies
"""
from backend.app.core.errors import ForbiddenException
from backend.app.identity.models import User


def can_manage_users(current_user: User) -> bool:
    if current_user.role != "admin":
        raise ForbiddenException("Only school administrators can create or manage user accounts")
    return True

