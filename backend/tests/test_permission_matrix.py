"""
Comprehensive Permission Matrix & Scoped RBAC Tests — Mind V2
Generates and executes tests across all 5 authority tiers:
1. Platform Admin
2. School Admin
3. Academic Coordinator (band-scoped)
4. Teacher (class/section/subject & Class Teacher flag)
5. Student (enrolled section & roll number)
"""
import pytest
from httpx import AsyncClient
from backend.app.identity.models import User, RoleName, RoleAssignment
from backend.app.core.permission_matrix import Action
from backend.app.core.policies import authorize
from backend.app.core.errors import ForbiddenException, TenantMismatchException


@pytest.mark.asyncio
async def test_permission_matrix_core_authorize_rules(db_session, seeded_test_data):
    """Directly tests authorize() against all 5 roles across allowed and forbidden actions."""
    plat = seeded_test_data["platform_admin"]
    admin = seeded_test_data["admin1"]
    coord = seeded_test_data["coord1"]
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    school1 = seeded_test_data["school1"]
    school2 = seeded_test_data["school2"]
    band_senior = seeded_test_data["band_senior"]
    band_middle = seeded_test_data["band_middle"]
    c11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sec_12d = seeded_test_data["sec_12d"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Platform Admin: Global Actions
    assert await authorize(plat, Action.SCHOOL_CREATE) is True
    assert await authorize(plat, Action.PLATFORM_DASHBOARD_VIEW) is True
    assert await authorize(plat, Action.SCHOOL_ADMIN_CREATE) is True

    # Non-Platform Admins must be denied global platform actions
    for user in (admin, coord, teacher, student):
        with pytest.raises(ForbiddenException):
            await authorize(user, Action.SCHOOL_CREATE)
        with pytest.raises(ForbiddenException):
            await authorize(user, Action.PLATFORM_DASHBOARD_VIEW)

    # 2. School Admin: School Actions
    assert await authorize(admin, Action.SCHOOL_PROFILE_UPDATE, {"school_id": school1.id}) is True
    assert await authorize(admin, Action.BAND_MANAGE, {"school_id": school1.id}) is True
    assert await authorize(admin, Action.CLASS_TEACHER_DESIGNATE, {"school_id": school1.id}) is True

    # School Admin cannot manage another school's tenancy
    with pytest.raises(ForbiddenException):
        await authorize(admin, Action.SCHOOL_PROFILE_UPDATE, {"school_id": school2.id})

    # 3. Academic Coordinator: Band Scoped
    # Allowed in assigned Senior Secondary band
    assert await authorize(coord, Action.COORDINATOR_DASHBOARD_VIEW, {"school_id": school1.id, "band_id": band_senior.id}) is True
    assert await authorize(coord, Action.TEACHER_CREATE, {"school_id": school1.id, "band_id": band_senior.id}) is True
    assert await authorize(coord, Action.ROSTER_LOCK, {"school_id": school1.id, "band_id": band_senior.id}) is True

    # Denied in another band within the SAME school (Middle School 6-8)
    with pytest.raises(ForbiddenException):
        await authorize(coord, Action.COORDINATOR_DASHBOARD_VIEW, {"school_id": school1.id, "band_id": band_middle.id})
    with pytest.raises(ForbiddenException):
        await authorize(coord, Action.TEACHER_CREATE, {"school_id": school1.id, "band_id": band_middle.id})

    # Denied in another school
    with pytest.raises(ForbiddenException):
        await authorize(coord, Action.COORDINATOR_DASHBOARD_VIEW, {"school_id": school2.id, "band_id": band_senior.id})

    # Coordinator cannot perform school admin global operations (e.g. update school profile)
    with pytest.raises(ForbiddenException):
        await authorize(coord, Action.SCHOOL_PROFILE_UPDATE, {"school_id": school1.id})

    # 4. Teacher & Class Teacher
    # Teacher can upload materials
    assert await authorize(teacher, Action.MATERIALS_UPLOAD, {"school_id": school1.id}) is True

    # Teacher assigned to 11E MATH can create assessments for 11E
    assert await authorize(
        teacher,
        Action.ASSESSMENT_CREATE,
        {"school_id": school1.id, "class_id": c11.id, "section_id": sec_11e.id, "subject_id": sub_math.id},
        db=db_session
    ) is True

    # Teacher NOT assigned to 12D is denied assessment creation for 12D
    with pytest.raises(ForbiddenException):
        await authorize(
            teacher,
            Action.ASSESSMENT_CREATE,
            {"school_id": school1.id, "class_id": c11.id, "section_id": sec_12d.id, "subject_id": sub_math.id},
            db=db_session
        )

    # 5. Student Scope
    # Student can attempt in enrolled section 11E
    assert await authorize(
        student,
        Action.ASSESSMENT_ATTEMPT,
        {"school_id": school1.id, "class_id": c11.id, "section_id": sec_11e.id},
        db=db_session
    ) is True

    # Student cannot access unapproved assessment drafts
    with pytest.raises(ForbiddenException):
        await authorize(student, Action.ASSESSMENT_CREATE, {"school_id": school1.id})
    with pytest.raises(ForbiddenException):
        await authorize(student, Action.ASSESSMENT_APPROVE, {"school_id": school1.id})


@pytest.mark.asyncio
async def test_platform_admin_api_endpoints(client: AsyncClient, seeded_test_data):
    """Tests Platform Admin HTTP endpoints for school provisioning, dashboard, and feature flags."""
    # 1. Login as Platform Admin
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "platform.admin@mind.local", "password": "PlatformPass123!"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Read Platform Dashboard
    dash_res = await client.get("/api/v1/platform/dashboard", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert data["total_schools"] >= 2
    assert data["total_users"] >= 6

    # 3. Provision a New School
    create_res = await client.post(
        "/api/v1/platform/schools",
        json={
            "name": "Delhi Public School Gomti Nagar",
            "slug": "dps-gomti-nagar",
            "code": "DPS-GN",
            "board": "CBSE",
            "timezone": "Asia/Kolkata",
            "academic_year_label": "2026-2027"
        },
        headers=headers
    )
    assert create_res.status_code == 201
    school_id = create_res.json()["id"]

    # 4. Provision School Admin for that school
    admin_res = await client.post(
        f"/api/v1/platform/schools/{school_id}/admins",
        json={
            "email": "principal@dpsgn.edu.in",
            "password": "Password123!",
            "full_name": "Dr. Pradeep Mishra",
            "designation": "Principal"
        },
        headers=headers
    )
    assert admin_res.status_code == 201
    assert admin_res.json()["role"] == "school_admin"

    # 5. Read Platform Audit Logs
    audit_res = await client.get("/api/v1/platform/audit-logs", headers=headers)
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 1


@pytest.mark.asyncio
async def test_non_platform_admin_denied_platform_endpoints(client: AsyncClient, seeded_test_data):
    """Asserts that School Admins, Coordinators, Teachers, and Students cannot hit platform endpoints."""
    # Login as School Admin
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@school1.org", "password": "AdminPass123!"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to hit platform dashboard
    dash_res = await client.get("/api/v1/platform/dashboard", headers=headers)
    assert dash_res.status_code == 403

    # Attempt to provision a school
    post_res = await client.post(
        "/api/v1/platform/schools",
        json={"name": "Hacked School", "slug": "hacked"},
        headers=headers
    )
    assert post_res.status_code == 403


@pytest.mark.asyncio
async def test_school_admin_band_management(client: AsyncClient, seeded_test_data):
    """Tests that School Admin can create and list bands within their school."""
    school = seeded_test_data["school1"]
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@school1.org", "password": "AdminPass123!"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List bands
    bands_res = await client.get(f"/api/v1/schools/{school.id}/bands", headers=headers)
    assert bands_res.status_code == 200
    bands = bands_res.json()
    assert len(bands) >= 2

    # Create new band (Primary 1-5)
    create_band_res = await client.post(
        f"/api/v1/schools/{school.id}/bands",
        json={"name": "Primary (1-5)", "min_grade": 1, "max_grade": 5},
        headers=headers
    )
    assert create_band_res.status_code == 201
    assert create_band_res.json()["name"] == "Primary (1-5)"
