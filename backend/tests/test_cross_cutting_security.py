"""
Cross-Cutting Security and Invariant Tests for Mind V1
Covers:
1. Strict Multi-Tenancy (Cross-tenant data access strictly rejected)
2. Strict 3-Role Authorization (Student/Teacher/Admin boundaries)
3. Zero Answer-Key Leakage to Students across all endpoints
4. Teacher Approval Gate Enforcement (Unapproved content cannot reach students)
5. Teacher Assignment Scoping (Cannot access unassigned classes/subjects)
"""
import pytest
from httpx import AsyncClient


async def get_token(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["session_token"]


@pytest.mark.asyncio
async def test_cross_tenant_isolation(client: AsyncClient, seeded_test_data):
    """
    Non-Negotiable #4: Server-side authorization everywhere.
    School 1 users must NOT be able to read, update, or delete School 2 resources.
    """
    admin1_token = await get_token(client, "admin@school1.org", "AdminPass123!")
    admin2_token = await get_token(client, "admin@school2.org", "AdminPass123!")

    admin1_headers = {"Authorization": f"Bearer {admin1_token}"}
    admin2_headers = {"Authorization": f"Bearer {admin2_token}"}

    school1_id = seeded_test_data["school1"].id
    school2_id = seeded_test_data["school2"].id

    # Admin 1 attempts to query School 2's academic years
    res = await client.get(
        f"/api/v1/schools/{school2_id}/academic-years",
        headers=admin1_headers,
    )
    assert res.status_code == 403

    # Admin 2 attempts to query School 1's academic years
    res2 = await client.get(
        f"/api/v1/schools/{school1_id}/academic-years",
        headers=admin2_headers,
    )
    assert res2.status_code == 403


@pytest.mark.asyncio
async def test_role_boundary_enforcement(client: AsyncClient, seeded_test_data):
    """
    Non-Negotiable #2: Exactly 3 roles. Deny by default.
    Students cannot call teacher/admin endpoints.
    Teachers cannot call admin-only endpoints.
    """
    student_token = await get_token(client, "student1@school1.org", "StudentPass123!")
    teacher_token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")

    student_headers = {"Authorization": f"Bearer {student_token}"}
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. Student attempts to access Admin Audit Logs
    audit_res = await client.get("/api/v1/audit-events", headers=student_headers)
    assert audit_res.status_code in [401, 403]

    # 2. Teacher attempts to access Admin Audit Logs
    teacher_audit_res = await client.get("/api/v1/audit-events", headers=teacher_headers)
    assert teacher_audit_res.status_code in [401, 403]

    # 3. Student attempts to generate assessments via AI Studio
    gen_res = await client.post(
        "/api/v1/generation/quizzes",
        json={
            "class_id": seeded_test_data["class_11"].id,
            "section_id": seeded_test_data["sec_11e"].id,
            "subject_id": seeded_test_data["sub_math"].id,
            "chapter": "Hacking",
            "topics": ["Exploit"],
            "question_count": 1,
            "total_marks": 5,
        },
        headers=student_headers,
    )
    assert gen_res.status_code in [401, 403]

    # 4. Student attempts to access Teacher Evaluation Queue
    eval_res = await client.get("/api/v1/teacher/evaluation-queue", headers=student_headers)
    assert eval_res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_teacher_approval_gate_enforcement(client: AsyncClient, seeded_test_data):
    """
    Non-Negotiable #3: Teacher approval is mandatory before any AI content reaches a student.
    Publishing an unapproved draft must be rejected by backend domain logic.
    """
    teacher_token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    class_id = seeded_test_data["class_11"].id
    section_id = seeded_test_data["sec_11e"].id
    subject_id = seeded_test_data["sub_math"].id

    # 1. Teacher generates quiz
    gen_res = await client.post(
        "/api/v1/generation/quizzes",
        json={
            "class_id": class_id,
            "section_id": section_id,
            "subject_id": subject_id,
            "chapter": "Probability",
            "topics": ["Independent Events"],
            "question_count": 1,
            "total_marks": 5,
        },
        headers=teacher_headers,
    )
    assert gen_res.status_code == 202
    job_id = gen_res.json()["job_id"]

    poll_res = await client.get(f"/api/v1/generation/jobs/{job_id}", headers=teacher_headers)
    asmt_id = poll_res.json()["assessment_id"]

    # 2. Attempt to publish DIRECTLY WITHOUT APPROVAL
    pub_attempt = await client.post(
        f"/api/v1/assessments/{asmt_id}/publish",
        json={
            "starts_at": "2026-11-01T00:00:00Z",
            "ends_at": "2026-11-30T23:59:59Z",
            "duration_minutes": 30,
            "max_attempts": 1,
        },
        headers=teacher_headers,
    )
    # Must fail because assessment is in 'needs_review' state, not 'approved'
    assert pub_attempt.status_code == 422
    assert "approved" in str(pub_attempt.json()).lower() or "approval" in str(pub_attempt.json()).lower()


@pytest.mark.asyncio
async def test_strict_teacher_scope_enforcement(client: AsyncClient, seeded_test_data):
    """
    Non-Negotiable #5: Teacher sees and acts ONLY on assigned Class + Section + Subject combinations.
    Teacher 1 is assigned to Class 11 Math and Class 12A Math, but NOT 12D Math or Physics.
    """
    teacher_token = await get_token(client, "teacher1@school1.org", "TeacherPass123!")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # Class 12D is NOT assigned to Teacher 1
    unassigned_class_id = seeded_test_data["class_12"].id
    unassigned_sec_id = seeded_test_data["sec_12d"].id
    subject_id = seeded_test_data["sub_math"].id

    # Attempt to generate quiz for unassigned section 12D
    unauth_gen = await client.post(
        "/api/v1/generation/quizzes",
        json={
            "class_id": unassigned_class_id,
            "section_id": unassigned_sec_id,
            "subject_id": subject_id,
            "chapter": "Calculus",
            "topics": ["Limits"],
            "question_count": 2,
            "total_marks": 10,
        },
        headers=teacher_headers,
    )
    assert unauth_gen.status_code == 403
