"""
Phase 2 Exit Gate Tests: AI Content Studio, 40 Question Types, Validation & Teacher Approval
"""
import pytest
from httpx import AsyncClient


async def get_token_for(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["session_token"]


@pytest.mark.asyncio
async def test_teacher_can_generate_edit_and_approve_assessment(client: AsyncClient, seeded_test_data):
    """
    Exit Gate Test Phase 2: A teacher produces, edits, and approves a usable draft.
    Teacher1 is assigned to Class 11 Section E (Mathematics).
    """
    teacher_token = await get_token_for(client, "teacher1@school1.org", "TeacherPass123!")
    class_id = seeded_test_data["class_11"].id
    section_id = seeded_test_data["sec_11e"].id
    subject_id = seeded_test_data["sub_math"].id

    # 1. Teacher generates a quiz with MCQs and Assertion-Reason
    gen_payload = {
        "class_id": class_id,
        "section_id": section_id,
        "subject_id": subject_id,
        "chapter": "Quadratic Equations",
        "topics": ["Nature of Roots", "Discriminant Method"],
        "difficulty": {"easy": 40, "medium": 60, "hard": 0},
        "question_count": 4,
        "total_marks": 8,
        "question_types": ["mcq", "assertion_reason", "fill_in_the_blanks", "short_answer"],
    }

    res_gen = await client.post(
        "/api/v1/generation/quizzes",
        json=gen_payload,
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_gen.status_code == 202
    job_id = res_gen.json()["job_id"]

    # 2. Poll job status
    res_job = await client.get(
        f"/api/v1/generation/jobs/{job_id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_job.status_code == 200
    job_detail = res_job.json()
    assert job_detail["status"] == "succeeded"
    assessment_id = job_detail["assessment_id"]
    assert assessment_id is not None

    # 3. Fetch Assessment Draft as Teacher
    res_draft = await client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_draft.status_code == 200
    draft = res_draft.json()
    assert draft["status"] == "needs_review"
    assert len(draft["items"]) == 4
    assert draft["total_marks"] == 8

    # Teacher sees answer keys and marking scheme
    first_item = draft["items"][0]
    assert first_item["question"]["answer_data"] is not None

    # 4. Teacher Edits Item #1 (Prompt and Marks)
    item_id = first_item["id"]
    res_edit = await client.patch(
        f"/api/v1/assessments/{assessment_id}/items/{item_id}",
        json={"prompt": "Customized prompt for Class 11E roots", "marks": 3},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_edit.status_code == 200
    updated_draft = res_edit.json()
    assert updated_draft["items"][0]["question"]["prompt"] == "Customized prompt for Class 11E roots"
    assert updated_draft["items"][0]["question"]["marks"] == 3

    # 5. Teacher Regenerates Single Item
    res_regen = await client.post(
        f"/api/v1/assessments/{assessment_id}/items/{item_id}/regenerate",
        json={"feedback": "Make it more challenging with negative coefficients"},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_regen.status_code == 200
    assert "Revised" in res_regen.json()["items"][0]["question"]["prompt"]

    # 6. Teacher Approves the Assessment
    res_approve = await client.post(
        f"/api/v1/assessments/{assessment_id}/approve",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_approve.status_code == 200
    approved_assessment = res_approve.json()
    assert approved_assessment["status"] == "approved"
    assert approved_assessment["version"] >= 2


@pytest.mark.asyncio
async def test_teacher_cannot_generate_for_unassigned_class(client: AsyncClient, seeded_test_data):
    """
    Teacher1 is assigned to 11E and 12A, but NOT 12D.
    Attempting to generate for 12D must be forbidden.
    """
    teacher_token = await get_token_for(client, "teacher1@school1.org", "TeacherPass123!")
    class_id = seeded_test_data["class_12"].id
    unassigned_section_id = seeded_test_data["sec_12d"].id
    subject_id = seeded_test_data["sub_math"].id

    res = await client.post(
        "/api/v1/generation/worksheets",
        json={
            "class_id": class_id,
            "section_id": unassigned_section_id,
            "subject_id": subject_id,
            "chapter": "Calculus",
            "topics": ["Limits"],
            "question_count": 5,
            "total_marks": 10,
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_access_unapproved_drafts(client: AsyncClient, seeded_test_data):
    """
    Non-negotiable #6 & #7: Student cannot access assessment drafts or unreleased answer keys.
    """
    teacher_token = await get_token_for(client, "teacher1@school1.org", "TeacherPass123!")
    student_token = await get_token_for(client, "student1@school1.org", "StudentPass123!")

    # 1. Create a draft as teacher
    gen_res = await client.post(
        "/api/v1/generation/quizzes",
        json={
            "class_id": seeded_test_data["class_11"].id,
            "section_id": seeded_test_data["sec_11e"].id,
            "subject_id": seeded_test_data["sub_math"].id,
            "chapter": "Algebra",
            "topics": ["Linear Inequalities"],
            "question_count": 2,
            "total_marks": 4,
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    job_id = gen_res.json()["job_id"]
    job_detail = (await client.get(f"/api/v1/generation/jobs/{job_id}", headers={"Authorization": f"Bearer {teacher_token}"})).json()
    assessment_id = job_detail["assessment_id"]

    # 2. Student attempts to read assessment draft -> Forbidden
    res_student = await client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_student.status_code == 403
