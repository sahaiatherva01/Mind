"""
Tests for Phase 2: Academic Coordinator & Assignment Matrix
Verifies:
1. Coordinator band summary metrics & class structure
2. Coordinator band isolation: cannot access or assign cross-band classes
3. Constraint enforcement: Exactly one Class Teacher designated per section (duplicate rejected with 409 Conflict)
4. Teacher onboarding within band: create and assign
5. Assignment Matrix retrieval: strictly band-scoped
6. Teacher status toggle: enabled/disabled within band
7. Curriculum viewer: filtered to band grades
"""
import pytest
from httpx import AsyncClient
from backend.app.identity.models import RoleName


async def get_token(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["session_token"]


@pytest.mark.asyncio
async def test_coordinator_band_summary(client: AsyncClient, seeded_test_data):
    """Coordinator can view band summary metrics for Senior Secondary (11-12)."""
    token = await get_token(client, "coord1@school1.org", "CoordPass123!")

    res = await client.get("/api/v1/coordinator/band-summary", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["band_name"] == "Senior Secondary (11-12)"
    assert data["min_grade"] == 11
    assert data["max_grade"] == 12
    assert data["total_classes"] == 2  # Class 11 and Class 12
    assert data["total_teachers"] >= 1
    # Check that class teacher for 11E is mapped
    sec_11e_id = seeded_test_data["sec_11e"].id
    assert sec_11e_id in data["class_teachers"]
    assert data["class_teachers"][sec_11e_id] == seeded_test_data["teacher1"].full_name


@pytest.mark.asyncio
async def test_coordinator_band_isolation_denies_cross_band(client: AsyncClient, seeded_test_data):
    """Coordinator of Classes 11-12 cannot assign a teacher to Class 9 (cross-band protection)."""
    token = await get_token(client, "coord1@school1.org", "CoordPass123!")
    class_9_id = seeded_test_data["class_9"].id
    sec_9a_id = seeded_test_data["sec_9a"].id
    sub_math_id = seeded_test_data["sub_math"].id
    teacher1_id = seeded_test_data["teacher1"].id

    payload = {
        "teacher_id": teacher1_id,
        "class_id": class_9_id,
        "section_id": sec_9a_id,
        "subject_id": sub_math_id,
        "is_class_teacher": False,
    }

    res = await client.post(
        "/api/v1/coordinator/assignments",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403, f"Expected 403 Forbidden for cross-band assignment, got: {res.status_code}"
    err = res.json()
    assert "band" in err["error"]["message"].lower() or "denied" in err["error"]["message"].lower()


@pytest.mark.asyncio
async def test_duplicate_class_teacher_rejected(client: AsyncClient, seeded_test_data):
    """Exactly one Class Teacher is allowed per section; assigning a second Class Teacher is rejected with 409 Conflict."""
    token = await get_token(client, "coord1@school1.org", "CoordPass123!")
    admin_token = await get_token(client, "admin@school1.org", "AdminPass123!")

    # 1. Create a second teacher in the school
    new_t_res = await client.post(
        "/api/v1/users",
        json={
            "email": "teacher2@school1.org",
            "password": "TeacherPass456!",
            "full_name": "Teacher Two",
            "role": "teacher",
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert new_t_res.status_code == 201
    teacher2_id = new_t_res.json()["id"]

    # 2. Section 11E already has teacher1 as Class Teacher (from seed)
    # Attempting to assign teacher2 as Class Teacher to Section 11E must fail with 409 Conflict
    class_11_id = seeded_test_data["class_11"].id
    sec_11e_id = seeded_test_data["sec_11e"].id
    sub_phy_id = seeded_test_data["sub_phy"].id

    res = await client.post(
        "/api/v1/coordinator/assignments",
        json={
            "teacher_id": teacher2_id,
            "class_id": class_11_id,
            "section_id": sec_11e_id,
            "subject_id": sub_phy_id,
            "is_class_teacher": True,  # Duplicate Class Teacher!
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 409, f"Expected 409 Conflict for duplicate Class Teacher, got: {res.status_code}"
    err = res.json()
    assert "class teacher" in err["error"]["message"].lower()


@pytest.mark.asyncio
async def test_coordinator_can_create_and_assign_teacher_within_band(client: AsyncClient, seeded_test_data):
    """Coordinator can provision a new teacher and assign them within their grade band."""
    token = await get_token(client, "coord1@school1.org", "CoordPass123!")
    class_12_id = seeded_test_data["class_12"].id
    sec_12d_id = seeded_test_data["sec_12d"].id
    sub_phy_id = seeded_test_data["sub_phy"].id

    payload = {
        "email": "physics.senior@school1.org",
        "full_name": "Sri Vikram Sen",
        "password": "TeacherPass123!",
        "designation": "PGT Physics Senior",
        "class_id": class_12_id,
        "section_id": sec_12d_id,
        "subject_id": sub_phy_id,
        "is_class_teacher": True,  # Section 12D has no class teacher yet, so this should succeed
    }

    res = await client.post(
        "/api/v1/coordinator/teachers",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["teacher"]["email"] == "physics.senior@school1.org"
    assert data["assignment"]["section_id"] == sec_12d_id
    assert data["assignment"]["is_class_teacher"] is True


@pytest.mark.asyncio
async def test_coordinator_assignment_matrix(client: AsyncClient, seeded_test_data):
    """Coordinator fetches assignment matrix containing only classes from their band."""
    token = await get_token(client, "coord1@school1.org", "CoordPass123!")

    res = await client.get("/api/v1/coordinator/assignments", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.text
    matrix = res.json()

    assert len(matrix) >= 2
    for item in matrix:
        assert item["class_name"] in ("Class 11", "Class 12")
        assert item["class_name"] != "Class 9"


@pytest.mark.asyncio
async def test_coordinator_teacher_status_toggle(client: AsyncClient, seeded_test_data):
    """Coordinator can deactivate and re-enable a teacher who teaches in their band."""
    token = await get_token(client, "coord1@school1.org", "CoordPass123!")
    teacher1_id = seeded_test_data["teacher1"].id

    # Deactivate teacher1
    res = await client.patch(
        f"/api/v1/coordinator/teachers/{teacher1_id}/status",
        json={"active": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "inactive"

    # Re-enable teacher1
    res_re = await client.patch(
        f"/api/v1/coordinator/teachers/{teacher1_id}/status",
        json={"active": True},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_re.status_code == 200, res_re.text
    assert res_re.json()["status"] == "active"
