"""
Platform Admin Router — Mind V2
Handles global management: Schools, Platform Dashboard, Feature Flags, Staff Provisioning.
Strictly restricted to users with RoleName.PLATFORM_ADMIN.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.identity.models import User, RoleName
from backend.app.identity.schemas import UserResponse, UserCreateRequest
from backend.app.identity import service as identity_service
from backend.app.tenancy import service as tenancy_service
from backend.app.tenancy.schemas import (
    SchoolResponse,
    SchoolCreateRequest,
    SchoolUpdateRequest,
    PlatformDashboardResponse,
    FeatureFlagUpdateRequest,
    SchoolAdminCreateRequest,
    CoordinatorCreateRequest,
)
from backend.app.audit.models import AuditEvent
from backend.app.audit.schemas import AuditEventResponse

router = APIRouter(prefix="/platform", tags=["Platform Administration"])


@router.get(
    "/dashboard",
    response_model=PlatformDashboardResponse,
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def get_platform_dashboard(db: AsyncSession = Depends(get_db)):
    return await tenancy_service.get_platform_dashboard_stats(db)


@router.get(
    "/schools",
    response_model=List[SchoolResponse],
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def list_all_schools(
    status: Optional[str] = Query(None, pattern="^(active|suspended|archived)$"),
    db: AsyncSession = Depends(get_db),
):
    schools = await tenancy_service.list_schools(db, status=status)
    return [SchoolResponse.model_validate(s) for s in schools]


@router.post(
    "/schools",
    response_model=SchoolResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def create_new_school(
    payload: SchoolCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    school = await tenancy_service.create_school(db, payload, actor_id=current_user.id)
    return SchoolResponse.model_validate(school)


@router.get(
    "/schools/{school_id}",
    response_model=SchoolResponse,
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def get_school_details(school_id: str, db: AsyncSession = Depends(get_db)):
    school = await tenancy_service.get_school_by_id(db, school_id)
    return SchoolResponse.model_validate(school)


@router.patch(
    "/schools/{school_id}",
    response_model=SchoolResponse,
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def update_school_details(
    school_id: str,
    payload: SchoolUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    school = await tenancy_service.update_school(db, school_id, payload, actor_id=current_user.id)
    return SchoolResponse.model_validate(school)


@router.post(
    "/schools/{school_id}/admins",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def create_school_admin(
    school_id: str,
    payload: SchoolAdminCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify school exists
    await tenancy_service.get_school_by_id(db, school_id)
    user_req = UserCreateRequest(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=RoleName.SCHOOL_ADMIN,
        designation=payload.designation,
    )
    user = await identity_service.create_user(db, school_id, user_req, actor_id=current_user.id)
    return UserResponse.model_validate(user)


@router.post(
    "/schools/{school_id}/coordinators",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def create_school_coordinator(
    school_id: str,
    payload: CoordinatorCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await tenancy_service.get_school_by_id(db, school_id)
    user_req = UserCreateRequest(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=RoleName.ACADEMIC_COORDINATOR,
        band_id=payload.band_id,
        designation=payload.designation,
    )
    user = await identity_service.create_user(db, school_id, user_req, actor_id=current_user.id)
    return UserResponse.model_validate(user)


@router.patch(
    "/schools/{school_id}/feature-flags",
    response_model=SchoolResponse,
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def update_feature_flags(
    school_id: str,
    payload: FeatureFlagUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    school = await tenancy_service.get_school_by_id(db, school_id)
    settings_dict = school.settings or {}
    flags = settings_dict.get("feature_flags", {})
    flags.update(payload.flags)
    settings_dict["feature_flags"] = flags

    update_req = SchoolUpdateRequest(settings=settings_dict)
    school = await tenancy_service.update_school(db, school_id, update_req, actor_id=current_user.id)
    return SchoolResponse.model_validate(school)


@router.get(
    "/audit-logs",
    response_model=List[AuditEventResponse],
    dependencies=[Depends(require_role([RoleName.PLATFORM_ADMIN]))],
)
async def list_platform_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return [AuditEventResponse.model_validate(e) for e in res.scalars().all()]
