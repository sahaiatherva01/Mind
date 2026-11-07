"""
Tenancy Business Logic Service
"""
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import ConflictException, NotFoundException
from backend.app.tenancy.models import School, AcademicYear
from backend.app.tenancy.schemas import SchoolCreateRequest, AcademicYearCreateRequest
from backend.app.audit.service import record_audit_event


async def create_school(db: AsyncSession, data: SchoolCreateRequest) -> School:
    slug_clean = data.slug.lower().strip()
    stmt = select(School).where(School.slug == slug_clean)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException(f"School slug '{slug_clean}' is already registered")

    school = School(
        name=data.name.strip(),
        slug=slug_clean,
        timezone=data.timezone,
        settings=data.settings or {},
    )
    db.add(school)
    await db.flush()
    return school


async def get_school_by_id(db: AsyncSession, school_id: str) -> School:
    stmt = select(School).where(School.id == school_id)
    res = await db.execute(stmt)
    school = res.scalar_one_or_none()
    if not school:
        raise NotFoundException("School", school_id)
    return school


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

    # If new year is active, demote existing active years
    if data.status == "active":
        demote_stmt = select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.status == "active"
        )
        res_active = await db.execute(demote_stmt)
        for old_year in res_active.scalars().all():
            old_year.status = "archived"

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
        metadata_json={"label": year.label, "status": year.status},
    )

    return year
