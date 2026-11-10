"""
Identity Business Logic Service
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.errors import (
    UnauthorizedException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from backend.app.core.security import (
    verify_password,
    hash_password,
    generate_secure_token,
    hash_session_token,
)
from backend.app.identity.models import User, Session, PasswordResetToken, RoleAssignment, RoleName
from backend.app.identity.schemas import UserCreateRequest, UserUpdateRequest
from backend.app.audit.service import record_audit_event


def canonicalize_role(raw_role: str) -> str:
    r = raw_role.lower().strip()
    if r in ("admin", "school_admin"):
        return RoleName.SCHOOL_ADMIN
    if r in ("platform_admin", "superadmin"):
        return RoleName.PLATFORM_ADMIN
    if r in ("coordinator", "academic_coordinator"):
        return RoleName.ACADEMIC_COORDINATOR
    if r in ("teacher", "faculty"):
        return RoleName.TEACHER
    if r in ("student", "pupil"):
        return RoleName.STUDENT
    return RoleName.STUDENT



async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> User:
    stmt = select(User).where(User.email == email.lower().strip())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedException("Invalid email or password")

    if user.status != "active":
        raise UnauthorizedException("Your account is currently disabled. Please contact your administrator.")

    return user


async def create_user_session(
    db: AsyncSession,
    user: User
) -> Tuple[Session, str]:
    raw_token = generate_secure_token(32)
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.SESSION_MAX_AGE_SECONDS)

    session = Session(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=user.school_id,
        actor_id=user.id,
        action="user.login",
        entity_type="session",
        entity_id=session.id,
    )

    return session, raw_token


async def terminate_session(
    db: AsyncSession,
    raw_token: str
) -> None:
    token_hash = hash_session_token(raw_token)
    stmt = select(Session).where(Session.token_hash == token_hash)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session:
        await db.delete(session)
        await db.flush()


async def initiate_password_reset(
    db: AsyncSession,
    email: str
) -> Optional[str]:
    stmt = select(User).where(User.email == email.lower().strip())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # To avoid email enumeration, silently return if user is not found
    if not user or user.status != "active":
        return None

    raw_token = generate_secure_token(32)
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)  # 2 hour validity

    reset_obj = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(reset_obj)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=user.school_id,
        actor_id=user.id,
        action="user.password_reset_requested",
        entity_type="user",
        entity_id=user.id,
    )

    return raw_token


async def complete_password_reset(
    db: AsyncSession,
    raw_token: str,
    new_password: str
) -> User:
    token_hash = hash_session_token(raw_token)
    stmt = (
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .where(PasswordResetToken.used_at.is_(None))
        .where(PasswordResetToken.expires_at > datetime.now(timezone.utc))
    )
    result = await db.execute(stmt)
    reset_record = result.scalar_one_or_none()

    if not reset_record:
        raise ValidationException("Invalid or expired password reset token")

    stmt_user = select(User).where(User.id == reset_record.user_id)
    user_res = await db.execute(stmt_user)
    user = user_res.scalar_one_or_none()

    if not user:
        raise NotFoundException("User", reset_record.user_id)

    user.password_hash = hash_password(new_password)
    reset_record.used_at = datetime.now(timezone.utc)

    # Invalidate all existing user sessions upon password reset
    del_stmt = select(Session).where(Session.user_id == user.id)
    res_sessions = await db.execute(del_stmt)
    for s in res_sessions.scalars().all():
        await db.delete(s)

    await db.flush()

    await record_audit_event(
        db=db,
        school_id=user.school_id,
        actor_id=user.id,
        action="user.password_reset_completed",
        entity_type="user",
        entity_id=user.id,
    )

    return user


async def create_user(
    db: AsyncSession,
    school_id: Optional[str],
    data: UserCreateRequest,
    actor_id: Optional[str] = None
) -> User:
    email_clean = data.email.lower().strip()
    if school_id:
        stmt = select(User).where(User.school_id == school_id, User.email == email_clean)
    else:
        stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException(f"A user with email '{email_clean}' already exists")

    canonical_role = canonicalize_role(data.role)

    new_user = User(
        school_id=school_id,
        email=email_clean,
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        designation=data.designation,
        status="active",
        must_change_password=(canonical_role == RoleName.STUDENT),
    )
    db.add(new_user)
    await db.flush()

    role_assignment = RoleAssignment(
        user_id=new_user.id,
        role=canonical_role,
        school_id=school_id,
        band_id=data.band_id,
        status="active",
    )
    db.add(role_assignment)
    await db.flush()

    new_user._cached_primary_role = canonical_role
    new_user.__dict__["role_assignments"] = [role_assignment]
    new_user._cached_role_assignments = [role_assignment]

    await record_audit_event(
        db=db,
        school_id=school_id or "PLATFORM",
        actor_id=actor_id,
        action="user.created",
        entity_type="user",
        entity_id=new_user.id,
        metadata_json={"role": canonical_role, "email": new_user.email},
    )

    return new_user


async def list_school_users(
    db: AsyncSession,
    school_id: str,
    role: Optional[str] = None,
    limit: int = 100
) -> List[User]:
    stmt = select(User).where(User.school_id == school_id)
    if role:
        canonical_role = canonicalize_role(role)
        stmt = stmt.join(RoleAssignment, User.id == RoleAssignment.user_id).where(
            RoleAssignment.role == canonical_role,
            RoleAssignment.status == "active"
        )
    stmt = stmt.order_by(User.full_name).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())

