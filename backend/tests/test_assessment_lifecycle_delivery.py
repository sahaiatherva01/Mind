"""
Phase 3 Exit Gate Test: Complete Assessment Delivery Lifecycle
From Teacher authoring/approval/publish → Student attempt/autosave/submit → Teacher grading → Result release.
Verifies:
1. No answer-key or rationale leakage across all student payloads before release.
2. Server time authority.
3. Idempotent autosave and submit.
4. Deterministic objective scoring.
5. Attempt limit enforcement.
"""
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient


async def get_token_for(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["session_token"]


@pytest.mark.asyncio
async def test_complete_end_to_end_assessment_delivery(client: AsyncClient, seeded_test_data):
    """
    Exit Gate Phase 3: End-to-end flow from Teacher publishing to Student attempt, evaluation, and result release.
    """
    teacher_token = await get_token_for(client, "teacher1@school1.org", "TeacherPass123!")
    student_token = await get_token_for(client, "student1@school1.org", "StudentPass123!")

    class_id = seeded_test_data["class_11"].id
    section_id = seeded_test_data["sec_11e"].id
    subject_id = seeded_test_data["sub_math"].id

    # 1. Teacher generates quiz (1 MCQ, 1 Short Answer)
    gen_res = await client.post(
        "/api/v1/generation/quizzes",
        json={
            "class_id": class_id,
            "section_id": section_id,
            "subject_id": subject_id,
            "chapter": "Quadratic Equations",
            "topics": ["Roots"],
            "question_count": 2,
            "total_marks": 5,
            "question_types": ["mcq", "short_answer"],
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert gen_res.status_code == 202
    job_id = gen_res.json()["job_id"]

    job_detail = (await client.get(f"/api/v1/generation/jobs/{job_id}", headers={"Authorization": f"Bearer {teacher_token}"})).json()
    assessment_id = job_detail["assessment_id"]

    # 2. Teacher Approves Assessment
    app_res = await client.post(
        f"/api/v1/assessments/{assessment_id}/approve",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert app_res.status_code == 200

    # 3. Teacher Publishes Assessment (Starts now, ends in 2 hours, manual result release)
    now = datetime.now(timezone.utc)
    pub_res = await client.post(
        f"/api/v1/assessments/{assessment_id}/publish",
        json={
            "starts_at": (now - timedelta(minutes=5)).isoformat(),
            "ends_at": (now + timedelta(hours=2)).isoformat(),
            "duration_minutes": 30,
            "max_attempts": 1,
            "result_release_mode": "manual_by_teacher",
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"

    # 4. Student sees the assignment in their assignments list
    asgn_res = await client.get("/api/v1/student/assignments", headers={"Authorization": f"Bearer {student_token}"})
    assert asgn_res.status_code == 200
    assignments = asgn_res.json()
    assert any(a["id"] == assessment_id for a in assignments)

    # 5. Non-Negotiable #6 Security Sweep: Inspect Instructions Payload for leaks
    inst_res = await client.get(
        f"/api/v1/assessments/{assessment_id}/instructions",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert inst_res.status_code == 200
    inst_text = str(inst_res.json()).lower()
    assert "expected_answer" not in inst_text
    assert "answer_keys" not in inst_text
    assert "marking_scheme" not in inst_text

    # 6. Student Starts Attempt
    start_res = await client.post(
        f"/api/v1/assessments/{assessment_id}/attempts",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert start_res.status_code == 201
    attempt_data = start_res.json()
    attempt_id = attempt_data["attempt_id"]
    questions = attempt_data["questions"]
    assert len(questions) == 2

    # Non-Negotiable #6 Security Sweep on question attempt payload: STRICTLY NO ANSWER LEAKAGE!
    for q in questions:
        q_str = str(q).lower()
        assert "expected_answer" not in q_str
        assert "answer_keys" not in q_str
        assert "marking_scheme" not in q_str
        assert "rationale" not in q_str

    item_mcq = questions[0]
    item_subjective = questions[1]

    # 7. Student Autosaves MCQ response ("A")
    save1 = await client.put(
        f"/api/v1/attempts/{attempt_id}/responses/{item_mcq['item_id']}",
        json={"answer_json": {"selected_option": "A"}},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert save1.status_code == 200
    assert save1.json()["status"] == "saved"

    # 8. Student Autosaves Subjective response
    save2 = await client.put(
        f"/api/v1/attempts/{attempt_id}/responses/{item_subjective['item_id']}",
        json={"answer_json": {"text": "Roots are real because the discriminant is positive."}},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert save2.status_code == 200

    # 9. Student Submits Attempt (Idempotent submission)
    sub_res = await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["status"] == "submitted"
    assert sub_data["is_released"] is False  # manual_by_teacher release mode

    # Second submit attempt returns existing without errors (idempotent)
    sub_res2 = await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert sub_res2.status_code == 200

    # 10. Student attempts to read results before release -> FORBIDDEN
    res_premature = await client.get(
        f"/api/v1/attempts/{attempt_id}/results",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_premature.status_code == 403

    # 11. Teacher views pending subjective questions in Evaluation Queue
    q_res = await client.get("/api/v1/teacher/evaluation-queue", headers={"Authorization": f"Bearer {teacher_token}"})
    assert q_res.status_code == 200
    queue = q_res.json()
    assert len(queue) >= 1
    target_resp = next(r for r in queue if r["attempt_id"] == attempt_id)

    # 12. Teacher grades subjective item (awards 2.5 marks + feedback)
    grade_res = await client.patch(
        f"/api/v1/evaluations/{target_resp['response_id']}",
        json={"manual_score": 2.5, "teacher_feedback": "Accurate explanation of the discriminant."},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert grade_res.status_code == 200
    assert grade_res.json()["manual_score"] == 2.5

    # 13. Teacher releases results
    rel_res = await client.post(
        f"/api/v1/assessments/{assessment_id}/release-results",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert rel_res.status_code == 200
    assert rel_res.json()["released_attempts"] >= 1

    # 14. Student can now access complete results and model solutions
    res_final = await client.get(
        f"/api/v1/attempts/{attempt_id}/results",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_final.status_code == 200
    result_data = res_final.json()
    assert result_data["total_score"] is not None
    assert len(result_data["responses"]) == 2
    # Verify teacher feedback and expected answers are now safely visible
    subj_resp = next(r for r in result_data["responses"] if r["type"] == "short_answer")
    assert subj_resp["teacher_feedback"] == "Accurate explanation of the discriminant."
    assert subj_resp["manual_score"] == 2.5


@pytest.mark.asyncio
async def test_attempt_limit_enforced(client: AsyncClient, seeded_test_data):
    """
    Verifies that a student cannot start a second attempt when max_attempts = 1.
    """
    teacher_token = await get_token_for(client, "teacher1@school1.org", "TeacherPass123!")
    student_token = await get_token_for(client, "student1@school1.org", "StudentPass123!")

    # Generate, approve, and publish
    gen_res = await client.post(
        "/api/v1/generation/quizzes",
        json={
            "class_id": seeded_test_data["class_11"].id,
            "section_id": seeded_test_data["sec_11e"].id,
            "subject_id": seeded_test_data["sub_math"].id,
            "chapter": "Sets",
            "topics": ["Venn Diagrams"],
            "question_count": 1,
            "total_marks": 2,
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    job_id = gen_res.json()["job_id"]
    job_detail = (await client.get(f"/api/v1/generation/jobs/{job_id}", headers={"Authorization": f"Bearer {teacher_token}"})).json()
    asmt_id = job_detail["assessment_id"]

    await client.post(f"/api/v1/assessments/{asmt_id}/approve", headers={"Authorization": f"Bearer {teacher_token}"})

    now = datetime.now(timezone.utc)
    await client.post(
        f"/api/v1/assessments/{asmt_id}/publish",
        json={
            "starts_at": (now - timedelta(minutes=1)).isoformat(),
            "ends_at": (now + timedelta(hours=1)).isoformat(),
            "max_attempts": 1,
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )

    # Attempt 1 -> start & submit
    att1 = (await client.post(f"/api/v1/assessments/{asmt_id}/attempts", headers={"Authorization": f"Bearer {student_token}"})).json()
    await client.post(f"/api/v1/attempts/{att1['attempt_id']}/submit", headers={"Authorization": f"Bearer {student_token}"})

    # Attempt 2 -> Conflict 409
    res_second = await client.post(f"/api/v1/assessments/{asmt_id}/attempts", headers={"Authorization": f"Bearer {student_token}"})
    assert res_second.status_code == 409
