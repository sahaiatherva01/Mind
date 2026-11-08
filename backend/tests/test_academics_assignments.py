"""
Tests for Teacher Assignments Scope, Student Enrollments, and Bulk Import
"""
import io
import pytest
from httpx import AsyncClient


async def get_token_for(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["session_token"]


@pytest.mark.asyncio
async def test_teacher_sees_only_assigned_workspaces(client: AsyncClient, seeded_test_data):
    """
    Non-negotiable #5: Teacher sees only assigned class/section/subject combinations.
    Teacher1 is assigned to 11E (MATH) and 12A (MATH), but NOT 12D.
    """
    teacher_token = await get_token_for(client, "teacher1@school1.org", "TeacherPass123!")

    # Fetch assignments as Teacher
    res = await client.get("/api/v1/teacher-assignments", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    assignments = res.json()

    # Teacher should see exactly their 2 assignments
    assert len(assignments) == 2
    assigned_keys = {(a["class_name"], a["section_name"], a["subject_name"]) for a in assignments}
    assert ("Class 11", "E", "Mathematics") in assigned_keys
    assert ("Class 12", "A", "Mathematics") in assigned_keys
    # Should NOT have Class 12 Section D
    assert not any(a["class_name"] == "Class 12" and a["section_name"] == "D" for a in assignments)


@pytest.mark.asyncio
async def test_bulk_import_csv(client: AsyncClient, seeded_test_data):
    """
    Admin can bulk import users, roles, classes, sections, and subjects via CSV with error reports.
    """
    admin_token = await get_token_for(client, "admin@school1.org", "AdminPass123!")

    csv_content = (
        "full_name,email,role,designation,class,section,subject\n"
        "Prof. Anita Roy,anita@school1.org,Teacher,Senior Teacher,Class 11,E,BIO\n"
        "Dr. Ramesh Head,ramesh@school1.org,Academic Coordinator,Coordinator,,,\n"
        "Kiran Student,kiran@school1.org,Student,,Class 11,E,\n"
        "Invalid Row,,Student,,Class 11,E,\n"  # Missing email -> Should generate row error
    )

    files = {
        "file": ("import.csv", csv_content.encode("utf-8"), "text/csv")
    }

    res = await client.post(
        "/api/v1/academics/bulk-import",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    report = res.json()

    assert report["total_rows"] == 4
    assert report["imported_count"] == 3
    assert report["error_count"] == 1
    assert len(report["errors"]) == 1
    assert report["errors"][0]["row_number"] == 5
    assert "Missing required email" in report["errors"][0]["error"]


@pytest.mark.asyncio
async def test_audit_logs_recorded_and_admin_restricted(client: AsyncClient, seeded_test_data):
    """
    Auditing records critical events. Only Admin can access /audit-events.
    """
    admin_token = await get_token_for(client, "admin@school1.org", "AdminPass123!")
    student_token = await get_token_for(client, "student1@school1.org", "StudentPass123!")

    # Student cannot view audit events
    s_res = await client.get("/api/v1/audit-events", headers={"Authorization": f"Bearer {student_token}"})
    assert s_res.status_code == 403

    # Admin can view audit events
    a_res = await client.get("/api/v1/audit-events", headers={"Authorization": f"Bearer {admin_token}"})
    assert a_res.status_code == 200
    events = a_res.json()["items"]
    assert len(events) > 0
    actions = [e["action"] for e in events]
    assert any("login" in a for a in actions)
