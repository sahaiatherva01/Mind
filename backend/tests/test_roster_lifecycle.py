"""
Tests for Phase 3: Teacher: Students, Rosters & Credentials
Verifies:
1. Class Teacher student addition with roll number
2. Non-Class Teacher (subject teacher only) denied adding students (403 Forbidden)
3. Duplicate roll number in same section rejected (409 Conflict)
4. Roster lifecycle: pending -> verified -> locked; direct additions blocked on locked roster
5. Post-lock RosterChangeRequest workflow (Teacher requests, Coordinator approves, student auto-enrolled)
6. Forced password change on first student login (must_change_password=True)
7. Credential distribution slips generation
"""
import pytest
from httpx import AsyncClient


async def get_token(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["session_token"]


@pytest.mark.asyncio
async def test_class_teacher_can_add_student(client: AsyncClient, seeded_test_data):
    """Class Teacher (teacher1 on 11E) can add a student with roll number and get credential slip."""
    token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")
    sec_11e_id = seeded_test_data["sec_11e"].id

    payload = {
        "full_name": "Devansh Roy",
        "roll_number": "11E-02",
    }

    res = await client.post(
        f"/api/v1/rosters/{sec_11e_id}/students",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["full_name"] == "Devansh Roy"
    assert data["roll_number"] == "11E-02"
    assert "mind.local" in data["login_email"]
    assert data["initial_password"] == "Mind@11E-02"
    assert data["must_change_password"] is True
    assert data["section_name"] == "E"


@pytest.mark.asyncio
async def test_non_class_teacher_denied_adding_student(client: AsyncClient, seeded_test_data):
    """A subject teacher who is NOT the designated Class Teacher is denied adding students (403 Forbidden)."""
    admin_token = await get_token(client, "admin@school1.org", "AdminPass123!")

    # 1. Create a subject teacher
    t_res = await client.post(
        "/api/v1/users",
        json={
            "email": "chem.teacher@school1.org",
            "password": "TeacherPass123!",
            "full_name": "Chemistry Subject Teacher",
            "role": "teacher",
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert t_res.status_code == 201
    chem_teacher_id = t_res.json()["id"]

    # 2. Assign as Chemistry subject teacher to 11E (is_class_teacher = False)
    class_11_id = seeded_test_data["class_11"].id
    sec_11e_id = seeded_test_data["sec_11e"].id
    sub_phy_id = seeded_test_data["sub_phy"].id

    asgn_res = await client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": chem_teacher_id,
            "class_id": class_11_id,
            "section_id": sec_11e_id,
            "subject_id": sub_phy_id,
            "is_class_teacher": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert asgn_res.status_code == 201

    # 3. Chem teacher logs in and attempts to add student to 11E -> 403 Forbidden!
    chem_token = await get_token(client, "chem.teacher@school1.org", "TeacherPass123!")

    res = await client.post(
        f"/api/v1/rosters/{sec_11e_id}/students",
        json={"full_name": "Unauthorized Student", "roll_number": "11E-99"},
        headers={"Authorization": f"Bearer {chem_token}"}
    )
    assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}"
    err = res.json()
    assert "class teacher" in err["error"]["message"].lower()


@pytest.mark.asyncio
async def test_duplicate_roll_number_rejected(client: AsyncClient, seeded_test_data):
    """Enforce roll number uniqueness per section; duplicate roll is rejected with 409 Conflict."""
    token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")
    sec_11e_id = seeded_test_data["sec_11e"].id

    # Roll 11E-01 was seeded in conftest
    res = await client.post(
        f"/api/v1/rosters/{sec_11e_id}/students",
        json={"full_name": "Duplicate Roll Candidate", "roll_number": "11E-01"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 409, f"Expected 409 Conflict, got {res.status_code}"
    err = res.json()
    assert "already assigned" in err["error"]["message"].lower()


@pytest.mark.asyncio
async def test_roster_lock_lifecycle_and_blocking(client: AsyncClient, seeded_test_data):
    """Roster transition to locked blocks direct student additions."""
    token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")
    sec_11e_id = seeded_test_data["sec_11e"].id

    # 1. Lock roster
    lock_res = await client.patch(
        f"/api/v1/rosters/{sec_11e_id}/status",
        json={"status": "locked"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert lock_res.status_code == 200
    assert lock_res.json()["roster_status"] == "locked"

    # 2. Direct student addition must fail with 409 Conflict
    add_res = await client.post(
        f"/api/v1/rosters/{sec_11e_id}/students",
        json={"full_name": "Blocked Direct Student", "roll_number": "11E-88"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert add_res.status_code == 409
    assert "locked" in add_res.json()["error"]["message"].lower()

    # Reset status to verified
    await client.patch(
        f"/api/v1/rosters/{sec_11e_id}/status",
        json={"status": "verified"},
        headers={"Authorization": f"Bearer {token}"}
    )


@pytest.mark.asyncio
async def test_post_lock_roster_change_request_workflow(client: AsyncClient, seeded_test_data):
    """Class Teacher requests post-lock change, Coordinator approves, student is auto-enrolled."""
    teacher_token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")
    coord_token = await get_token(client, "coordinator@school1.org", "CoordPass123!")
    sec_11e_id = seeded_test_data["sec_11e"].id

    # 1. Lock the roster
    await client.patch(
        f"/api/v1/rosters/{sec_11e_id}/status",
        json={"status": "locked"},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )

    # 2. Class Teacher submits change request
    req_res = await client.post(
        f"/api/v1/rosters/{sec_11e_id}/change-requests",
        json={
            "change_type": "add_student",
            "student_data": {"full_name": "Late Transfer Student", "roll_number": "11E-50"},
            "reason": "Principal approved mid-term transfer",
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert req_res.status_code == 201, req_res.text
    req_id = req_res.json()["id"]
    assert req_res.json()["status"] == "pending"

    # 3. Coordinator approves request
    review_res = await client.patch(
        f"/api/v1/rosters/change-requests/{req_id}/review",
        json={"status": "approved", "review_notes": "Transfer papers verified."},
        headers={"Authorization": f"Bearer {coord_token}"}
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "approved"

    # 4. Verify student is now enrolled in roster
    roster_res = await client.get(
        f"/api/v1/rosters/{sec_11e_id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert roster_res.status_code == 200
    rolls = [s["roll_number"] for s in roster_res.json()["students"]]
    assert "11E-50" in rolls


@pytest.mark.asyncio
async def test_forced_password_change_on_first_login(client: AsyncClient, seeded_test_data):
    """Newly added students must change their password on first login."""
    token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")
    sec_12a_id = seeded_test_data["sec_12a"].id

    # Teacher1 assigns student to 12A via Admin
    admin_token = await get_token(client, "admin@school1.org", "AdminPass123!")
    slip_res = await client.post(
        f"/api/v1/rosters/{sec_12a_id}/students",
        json={"full_name": "Kavya Sharma", "roll_number": "12A-09"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert slip_res.status_code == 201
    slip = slip_res.json()

    # Login as student
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": slip["login_email"], "password": slip["initial_password"]}
    )
    assert login_res.status_code == 200
    user_data = login_res.json()["user"]
    assert user_data["must_change_password"] is True


@pytest.mark.asyncio
async def test_credential_slips_generation(client: AsyncClient, seeded_test_data):
    """Class Teacher can generate printable credential slips for the section."""
    token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")
    sec_11e_id = seeded_test_data["sec_11e"].id

    res = await client.get(
        f"/api/v1/rosters/{sec_11e_id}/credentials",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200, res.text
    slips = res.json()
    assert len(slips) >= 1
    for s in slips:
        assert "login_email" in s
        assert "initial_password" in s
        assert s["section_name"] == "E"

