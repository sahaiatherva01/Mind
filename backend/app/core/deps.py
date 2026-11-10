"""
FastAPI Dependencies for Authentication, Session Resolution, Tenancy and RBAC
"""
from datetime import datetime, timezone
from typing import Optional, List, Union
from fastapi import Depends, Request, Header, Cookie
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core.errors import UnauthorizedException, ForbiddenException, NotFoundException
from backend.app.core.security import hash_session_token
from backend.app.identity.models import Session, User


async def get_current_session_token(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """
    Extracts session token from Authorization: Bearer <token> header or HttpOnly cookie.
    Explicit Authorization header takes precedence.
    """
    # 1. Check Authorization Bearer header first
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()

    # 2. Fallback to session cookie
    cookie_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


async def get_current_user(
    token: Optional[str] = Depends(get_current_session_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise UnauthorizedException("Authentication token or session cookie missing")

    token_hash = hash_session_token(token)
    stmt = (
        select(Session)
        .where(Session.token_hash == token_hash)
        .where(Session.expires_at > datetime.now(timezone.utc))
    )
    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()

    if not session_obj:
        raise UnauthorizedException("Invalid or expired session. Please log in again.")

    # Update last_active_at
    session_obj.last_active_at = datetime.now(timezone.utc)

    # Fetch user
    user_stmt = select(User).where(User.id == session_obj.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user or user.status != "active":
        raise UnauthorizedException("User account is inactive or not found")

    return user


from backend.app.identity.models import User, RoleName, RoleAssignment
from backend.app.core.policies import authorize
from backend.app.core.permission_matrix import Action


def require_role(allowed_roles: Union[str, List[str]]):
    if isinstance(allowed_roles, str):
        target_roles = {allowed_roles}
    else:
        target_roles = set(allowed_roles)

    # Expand legacy aliases for backward compatibility
    if "admin" in target_roles:
        target_roles.update([RoleName.PLATFORM_ADMIN, RoleName.SCHOOL_ADMIN])

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = {r.role for r in current_user.role_assignments if r.status == "active"}
        if not user_roles.intersection(target_roles):
            raise ForbiddenException(
                f"Action requires one of the following roles: {', '.join(sorted(target_roles))}. "
                f"Your active roles are: {', '.join(sorted(user_roles)) or 'none'}."
            )
        return current_user

    return role_checker


def require_permission(action: str):
    """Dependency that authorizes an action using the central policy engine."""
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        await authorize(current_user, action, db=db)
        return current_user

    return permission_checker



async def get_active_school_id(current_user: User = Depends(get_current_user)) -> str:
    """Returns the tenant school_id of the currently authenticated user."""
    return current_user.school_id
