"""
Tenancy Router: Schools, Academic Years, Bands, and Settings — Mind V2
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.tenancy import service, policies
from backend.app.tenancy.schemas import (
    SchoolResponse,
    SchoolUpdateRequest,
    AcademicYearResponse,
    AcademicYearCreateRequest,
    BandResponse,
    BandCreateRequest,
)

router = APIRouter(prefix="/schools", tags=["Tenancy"])


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_tenancy(current_user, school_id)
    school = await service.get_school_by_id(db, school_id)
    return SchoolResponse.model_validate(school)


@router.patch("/{school_id}/profile", response_model=SchoolResponse)
async def update_school_profile(
    school_id: str,
    payload: SchoolUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_tenancy(current_user, school_id)
    school = await service.update_school(db, school_id, payload, actor_id=current_user.id)
    return SchoolResponse.model_validate(school)


@router.get("/{school_id}/bands", response_model=List[BandResponse])
async def list_school_bands(
    school_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_tenancy(current_user, school_id)
    bands = await service.list_bands(db, school_id)
    return [BandResponse.model_validate(b) for b in bands]


@router.post(
    "/{school_id}/bands",
    response_model=BandResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_school_band(
    school_id: str,
    payload: BandCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_tenancy(current_user, school_id)
    band = await service.create_band(db, school_id, payload)
    return BandResponse.model_validate(band)


@router.get("/{school_id}/academic-years", response_model=List[AcademicYearResponse])
async def list_academic_years(
    school_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_tenancy(current_user, school_id)
    years = await service.list_academic_years(db, school_id)
    return [AcademicYearResponse.model_validate(y) for y in years]


@router.post(
    "/{school_id}/academic-years",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_academic_year(
    school_id: str,
    payload: AcademicYearCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_tenancy(current_user, school_id)
    year = await service.create_academic_year(
        db=db,
        school_id=school_id,
        data=payload,
        actor_id=current_user.id,
    )
    return AcademicYearResponse.model_validate(year)


@router.patch("/{school_id}/settings", response_model=SchoolResponse)
async def update_school_settings(
    school_id: str,
    settings_payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_tenancy(current_user, school_id)
    update_req = SchoolUpdateRequest(settings=settings_payload)
    school = await service.update_school(db, school_id, update_req, actor_id=current_user.id)
    return SchoolResponse.model_validate(school)
