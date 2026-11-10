"""
Pytest Fixtures for Backend Test Suite
"""
import os
os.environ["ENVIRONMENT"] = "test"
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.app.core.config import settings
settings.ENVIRONMENT = "test"
from backend.app.core.db import Base, get_db
from backend.app.core.security import hash_password
from backend.app.main import app

# Test database engine: uses Postgres if TEST_DATABASE_URL or DATABASE_URL specifies postgresql
TEST_DB_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DB_URL:
    db_env = os.getenv("DATABASE_URL", "")
    if "postgresql" in db_env:
        TEST_DB_URL = db_env
    else:
        TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine_kwargs = {}
if "sqlite" in TEST_DB_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

test_engine = create_async_engine(TEST_DB_URL, **engine_kwargs)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def seeded_test_data(db_session: AsyncSession):
    from datetime import date
    from backend.app.tenancy.models import School, AcademicYear, Band
    from backend.app.identity.models import User, RoleAssignment, RoleName
    from backend.app.academics.models import Class, Section, Subject, TeacherAssignment, StudentEnrollment

    # School 1 (Primary)
    school1 = School(name="Springfield Academy", slug="springfield", code="SPF", timezone="Asia/Kolkata")
    # School 2 (Second Tenant for Cross-Tenant tests)
    school2 = School(name="Shelbyville High", slug="shelbyville", code="SHB", timezone="Asia/Kolkata")
    db_session.add_all([school1, school2])
    await db_session.flush()

    # Bands for School 1
    band_middle = Band(school_id=school1.id, name="Middle School (6-8)", min_grade=6, max_grade=8)
    band_senior = Band(school_id=school1.id, name="Senior Secondary (11-12)", min_grade=11, max_grade=12)
    db_session.add_all([band_middle, band_senior])
    await db_session.flush()

    # Academic Year
    year1 = AcademicYear(school_id=school1.id, label="2026-2027", starts_on=date(2026, 4, 1), ends_on=date(2027, 3, 31), status="active")
    year2 = AcademicYear(school_id=school2.id, label="2026-2027", starts_on=date(2026, 4, 1), ends_on=date(2027, 3, 31), status="active")
    db_session.add_all([year1, year2])
    await db_session.flush()

    # Platform Admin (Global, no school)
    platform_admin = User(
        school_id=None,
        email="platform.admin@mind.local",
        password_hash=hash_password("PlatformPass123!"),
        full_name="Platform Overseer",
        status="active"
    )

    # Users for School 1
    admin1 = User(
        school_id=school1.id,
        email="admin@school1.org",
        password_hash=hash_password("AdminPass123!"),
        full_name="Admin One",
        status="active"
    )
    coord1 = User(
        school_id=school1.id,
        email="coordinator@school1.org",
        password_hash=hash_password("CoordPass123!"),
        full_name="Coordinator Senior",
        status="active"
    )
    teacher1 = User(
        school_id=school1.id,
        email="teacher1@school1.org",
        password_hash=hash_password("TeacherPass123!"),
        full_name="Maths Teacher",
        status="active"
    )
    student1 = User(
        school_id=school1.id,
        email="student1@school1.org",
        password_hash=hash_password("StudentPass123!"),
        full_name="Student One",
        status="active"
    )

    # Users for School 2
    admin2 = User(
        school_id=school2.id,
        email="admin@school2.org",
        password_hash=hash_password("AdminPass123!"),
        full_name="Admin Two",
        status="active"
    )

    db_session.add_all([platform_admin, admin1, coord1, teacher1, student1, admin2])
    await db_session.flush()

    # Role Assignments
    ra_platform = RoleAssignment(user_id=platform_admin.id, role=RoleName.PLATFORM_ADMIN, school_id=None, status="active")
    ra_admin1 = RoleAssignment(user_id=admin1.id, role=RoleName.SCHOOL_ADMIN, school_id=school1.id, status="active")
    ra_coord1 = RoleAssignment(user_id=coord1.id, role=RoleName.ACADEMIC_COORDINATOR, school_id=school1.id, band_id=band_senior.id, status="active")
    ra_teacher1 = RoleAssignment(user_id=teacher1.id, role=RoleName.TEACHER, school_id=school1.id, status="active")
    ra_student1 = RoleAssignment(user_id=student1.id, role=RoleName.STUDENT, school_id=school1.id, status="active")
    ra_admin2 = RoleAssignment(user_id=admin2.id, role=RoleName.SCHOOL_ADMIN, school_id=school2.id, status="active")

    db_session.add_all([ra_platform, ra_admin1, ra_coord1, ra_teacher1, ra_student1, ra_admin2])
    await db_session.flush()

    # Academics for School 1
    class_11 = Class(school_id=school1.id, academic_year_id=year1.id, name="Class 11")
    class_12 = Class(school_id=school1.id, academic_year_id=year1.id, name="Class 12")
    db_session.add_all([class_11, class_12])
    await db_session.flush()

    sec_11e = Section(class_id=class_11.id, name="E")
    sec_12a = Section(class_id=class_12.id, name="A")
    sec_12d = Section(class_id=class_12.id, name="D")
    db_session.add_all([sec_11e, sec_12a, sec_12d])
    await db_session.flush()

    sub_math = Subject(school_id=school1.id, name="Mathematics", code="MATH")
    sub_phy = Subject(school_id=school1.id, name="Physics", code="PHY")
    db_session.add_all([sub_math, sub_phy])
    await db_session.flush()

    # Assign Teacher1 to 11E (MATH) and 12A (MATH), but NOT 12D
    asgn_11e = TeacherAssignment(
        school_id=school1.id,
        teacher_id=teacher1.id,
        class_id=class_11.id,
        section_id=sec_11e.id,
        subject_id=sub_math.id
    )
    asgn_12a = TeacherAssignment(
        school_id=school1.id,
        teacher_id=teacher1.id,
        class_id=class_12.id,
        section_id=sec_12a.id,
        subject_id=sub_math.id
    )
    db_session.add_all([asgn_11e, asgn_12a])

    # Enroll Student1 in 11E
    enroll1 = StudentEnrollment(
        school_id=school1.id,
        student_id=student1.id,
        class_id=class_11.id,
        section_id=sec_11e.id,
        roll_number="11E-01",
        status="active"
    )
    db_session.add(enroll1)

    await db_session.flush()

    for u, ra in [
        (platform_admin, ra_platform),
        (admin1, ra_admin1),
        (coord1, ra_coord1),
        (teacher1, ra_teacher1),
        (student1, ra_student1),
        (admin2, ra_admin2),
    ]:
        u._cached_role_assignments = [ra]
        u.__dict__["role_assignments"] = [ra]

    return {
        "school1": school1,
        "school2": school2,
        "platform_admin": platform_admin,
        "admin1": admin1,
        "coord1": coord1,
        "teacher1": teacher1,
        "student1": student1,
        "admin2": admin2,
        "band_middle": band_middle,
        "band_senior": band_senior,
        "class_11": class_11,
        "class_12": class_12,
        "sec_11e": sec_11e,
        "sec_12a": sec_12a,
        "sec_12d": sec_12d,
        "sub_math": sub_math,
        "sub_phy": sub_phy,
    }
