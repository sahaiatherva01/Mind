"""
Tests for Multi-Tenancy Isolation and Strict Role-Based Access Control (RBAC)
"""
import pytest
from httpx import AsyncClient


async def get_token_for(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["session_token"]


@pytest.mark.asyncio
async def test_cross_tenant_isolation_denied(client: AsyncClient, seeded_test_data):
    """
    Exit Gate Test: A user (even an Admin) from School 2 must NEVER access or modify School 1 data.
    """
    school1_id = seeded_test_data["school1"].id
    school2_id = seeded_test_data["school2"].id

    admin2_token = await get_token_for(client, "admin@school2.org", "AdminPass123!")

    # Admin 2 attempts to fetch School 1 details -> Forbidden
    res = await client.get(
        f"/api/v1/schools/{school1_id}",
        headers={"Authorization": f"Bearer {admin2_token}"}
    )
    assert res.status_code == 403
    err = res.json()
    assert err["error"]["code"] == "FORBIDDEN"

    # Admin 2 attempts to list School 1 academic years -> Forbidden
    res_years = await client.get(
        f"/api/v1/schools/{school1_id}/academic-years",
        headers={"Authorization": f"Bearer {admin2_token}"}
    )
    assert res_years.status_code == 403


@pytest.mark.asyncio
async def test_rbac_teacher_and_student_cannot_administer(client: AsyncClient, seeded_test_data):
    """
    Exit Gate Test: Teachers and Students cannot create classes, subjects, or academic years.
    """
    school1_id = seeded_test_data["school1"].id
    year1_id = seeded_test_data["class_11"].academic_year_id

    teacher_token = await get_token_for(client, "teacher1@school1.org", "TeacherPass123!")
    student_token = await get_token_for(client, "student1@school1.org", "StudentPass123!")

    # 1. Teacher attempts to create a class -> Forbidden
    res_t_class = await client.post(
        "/api/v1/classes",
        json={"academic_year_id": year1_id, "name": "Unauthorized Class"},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_t_class.status_code == 403

    # 2. Student attempts to create a subject -> Forbidden
    res_s_sub = await client.post(
        "/api/v1/subjects",
        json={"name": "Hacking 101", "code": "HACK"},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_s_sub.status_code == 403

    # 3. Teacher attempts to create a user -> Forbidden
    res_t_user = await client.post(
        "/api/v1/users",
        json={"email": "newbie@school1.org", "password": "Password123!", "full_name": "Newbie", "role": "student"},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_t_user.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_manage_academic_setup(client: AsyncClient, seeded_test_data):
    """
    Admin has full authorized control within their own school.
    """
    admin1_token = await get_token_for(client, "admin@school1.org", "AdminPass123!")
    year1_id = seeded_test_data["class_11"].academic_year_id

    # Create new class
    res = await client.post(
        "/api/v1/classes",
        json={"academic_year_id": year1_id, "name": "Class 9", "section_names": ["A", "B"]},
        headers={"Authorization": f"Bearer {admin1_token}"}
    )
    assert res.status_code == 201
    created_class = res.json()
    assert created_class["name"] == "Class 9"
    assert len(created_class["sections"]) == 2
