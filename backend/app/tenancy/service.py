"""
Tenancy Business Logic Service — Mind V2
Supports School lifecycle, Bands, Academic Years, and Platform Administration.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import ConflictException, NotFoundException, ValidationException
from backend.app.tenancy.models import School, AcademicYear, Band
from backend.app.identity.models import User
from backend.app.assessments.models import Assessment
from backend.app.tenancy.schemas import (
    SchoolCreateRequest,
    SchoolUpdateRequest,
    AcademicYearCreateRequest,
    BandCreateRequest,
    PlatformDashboardResponse,
)
from backend.app.audit.service import record_audit_event


async def create_school(db: AsyncSession, data: SchoolCreateRequest, actor_id: Optional[str] = None) -> School:
    slug_clean = data.slug.lower().strip()
    stmt = select(School).where(School.slug == slug_clean)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException(f"School slug '{slug_clean}' is already registered")

    if data.code:
        code_stmt = select(School).where(School.code == data.code.strip())
        code_res = await db.execute(code_stmt)
        if code_res.scalar_one_or_none():
            raise ConflictException(f"School code '{data.code}' is already registered")

    settings_dict = data.settings or {}
    # Default feature flags if not set
    if "feature_flags" not in settings_dict:
        settings_dict["feature_flags"] = {
            "online_exams": True,
            "ai_studio": True,
            "report_cards": True,
            "ocr_grading": False,
        }

    school = School(
        name=data.name.strip(),
        slug=slug_clean,
        code=data.code.strip() if data.code else None,
        board=data.board or "ICSE/ISC",
        status="active",
        timezone=data.timezone,
        settings=settings_dict,
    )
    db.add(school)
    await db.flush()

    # Create default bands for Indian ICSE/ISC schools (Middle 6–8, Secondary 9–10, Senior Secondary 11–12)
    default_bands = [
        {"name": "Middle School (6–8)", "min_grade": 6, "max_grade": 8},
        {"name": "Secondary (9–10)", "min_grade": 9, "max_grade": 10},
        {"name": "Senior Secondary (11–12)", "min_grade": 11, "max_grade": 12},
    ]
    for b in default_bands:
        band = Band(
            school_id=school.id,
            name=b["name"],
            min_grade=b["min_grade"],
            max_grade=b["max_grade"],
        )
        db.add(band)

    # Create default academic year
    if data.academic_year_label:
        ay = AcademicYear(
            school_id=school.id,
            label=data.academic_year_label,
            starts_on=date(2026, 4, 1),
            ends_on=date(2027, 3, 31),
            status="active",
        )
        db.add(ay)

    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school.id,
        actor_id=actor_id or "PLATFORM",
        action="school.created",
        entity_type="school",
        entity_id=school.id,
        metadata_json={"name": school.name, "slug": school.slug},
    )

    return school


async def update_school(db: AsyncSession, school_id: str, data: SchoolUpdateRequest, actor_id: Optional[str] = None) -> School:
    school = await get_school_by_id(db, school_id)

    if data.name is not None:
        school.name = data.name.strip()
    if data.code is not None:
        school.code = data.code.strip()
    if data.board is not None:
        school.board = data.board.strip()
    if data.timezone is not None:
        school.timezone = data.timezone
    if data.status is not None:
        school.status = data.status
    if data.settings is not None:
        current_settings = school.settings or {}
        current_settings.update(data.settings)
        school.settings = current_settings

    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school.id,
        actor_id=actor_id,
        action="school.updated",
        entity_type="school",
        entity_id=school.id,
    )
    return school


async def list_schools(db: AsyncSession, status: Optional[str] = None) -> List[School]:
    stmt = select(School)
    if status:
        stmt = stmt.where(School.status == status)
    stmt = stmt.order_by(School.name)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_school_by_id(db: AsyncSession, school_id: str) -> School:
    stmt = select(School).where(School.id == school_id)
    res = await db.execute(stmt)
    school = res.scalar_one_or_none()
    if not school:
        raise NotFoundException("School", school_id)
    return school


# --- Band Management ---

async def list_bands(db: AsyncSession, school_id: str) -> List[Band]:
    stmt = select(Band).where(Band.school_id == school_id).order_by(Band.min_grade)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def create_band(db: AsyncSession, school_id: str, data: BandCreateRequest) -> Band:
    if data.min_grade > data.max_grade:
        raise ValidationException("min_grade cannot exceed max_grade")

    stmt = select(Band).where(Band.school_id == school_id, Band.name == data.name.strip())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException(f"Band '{data.name}' already exists in this school")

    band = Band(
        school_id=school_id,
        name=data.name.strip(),
        min_grade=data.min_grade,
        max_grade=data.max_grade,
    )
    db.add(band)
    await db.flush()
    return band


# --- Academic Years ---

async def list_academic_years(db: AsyncSession, school_id: str) -> List[AcademicYear]:
    stmt = (
        select(AcademicYear)
        .where(AcademicYear.school_id == school_id)
        .order_by(AcademicYear.starts_on.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def create_academic_year(
    db: AsyncSession,
    school_id: str,
    data: AcademicYearCreateRequest,
    actor_id: Optional[str] = None
) -> AcademicYear:
    stmt = select(AcademicYear).where(
        AcademicYear.school_id == school_id,
        AcademicYear.label == data.label.strip()
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException(f"Academic year '{data.label}' already exists for this school")

    year = AcademicYear(
        school_id=school_id,
        label=data.label.strip(),
        starts_on=data.starts_on,
        ends_on=data.ends_on,
        status=data.status,
    )
    db.add(year)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="academic_year.created",
        entity_type="academic_year",
        entity_id=year.id,
        metadata_json={"label": year.label},
    )

    return year


# --- Platform Dashboard Metrics ---

async def get_platform_dashboard_stats(db: AsyncSession) -> PlatformDashboardResponse:
    school_count_res = await db.execute(select(func.count(School.id)))
    total_schools = school_count_res.scalar() or 0

    user_count_res = await db.execute(select(func.count(User.id)))
    total_users = user_count_res.scalar() or 0

    active_user_res = await db.execute(select(func.count(User.id)).where(User.status == "active"))
    active_users = active_user_res.scalar() or 0

    assess_count_res = await db.execute(select(func.count(Assessment.id)))
    total_assessments = assess_count_res.scalar() or 0

    return PlatformDashboardResponse(
        total_schools=total_schools,
        total_users=total_users,
        active_users=active_users,
        total_assessments=total_assessments,
    )
