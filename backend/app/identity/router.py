"""
Identity & Authentication Router
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Response, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user, get_current_session_token
from backend.app.identity import service, policies
from backend.app.identity.models import User
from backend.app.identity.schemas import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    UserCreateRequest,
    MeResponse,
    SchoolSummaryResponse,
)
from backend.app.tenancy.models import School, AcademicYear

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
user_router = APIRouter(prefix="/users", tags=["Users"])


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await service.authenticate_user(db, payload.email, payload.password)
    session, raw_token = await service.create_user_session(db, user)

    # Set secure HttpOnly session cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite=settings.SAME_SITE,
        path="/",
    )

    return LoginResponse(
        user=UserResponse.model_validate(user),
        session_token=raw_token,
        expires_at=session.expires_at,
    )


@auth_router.post("/logout")
async def logout(
    response: Response,
    token: Optional[str] = Depends(get_current_session_token),
    db: AsyncSession = Depends(get_db),
):
    if token:
        await service.terminate_session(db, token)

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite=settings.SAME_SITE,
    )
    return {"message": "Successfully logged out"}


@auth_router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    raw_token = await service.initiate_password_reset(db, payload.email)
    # In dev/test mode, return the token directly to facilitate testing
    dev_token = raw_token if settings.ENVIRONMENT in ("development", "test") else None
    return ForgotPasswordResponse(
        message="If an account exists with that email address, password reset instructions have been sent.",
        reset_token_dev=dev_token,
    )


@auth_router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    await service.complete_password_reset(db, payload.token, payload.new_password)
    return {"message": "Password has been successfully reset. Please log in with your new password."}


@auth_router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(School).where(School.id == current_user.school_id)
    res = await db.execute(stmt)
    school = res.scalar_one()

    # Active academic year if any
    year_stmt = select(AcademicYear).where(
        AcademicYear.school_id == current_user.school_id,
        AcademicYear.status == "active"
    ).limit(1)
    year_res = await db.execute(year_stmt)
    active_year = year_res.scalar_one_or_none()

    return MeResponse(
        user=UserResponse.model_validate(current_user),
        school=SchoolSummaryResponse.model_validate(school),
        active_academic_year_id=active_year.id if active_year else None,
    )


@user_router.get("", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = Query(None, pattern="^(admin|teacher|student)$"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_users(current_user)
    users = await service.list_school_users(db, current_user.school_id, role=role, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@user_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    payload: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_users(current_user)
    new_user = await service.create_user(
        db=db,
        school_id=current_user.school_id,
        data=payload,
        actor_id=current_user.id
    )
    return UserResponse.model_validate(new_user)

