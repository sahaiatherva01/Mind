import pytest
from httpx import AsyncClient


async def get_token_for(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["session_token"]


@pytest.mark.asyncio
async def test_analytics_and_exports_flow(client: AsyncClient, seeded_test_data):
    teacher_token = await get_token_for(client, "teacher1@school1.org", "TeacherPass123!")
    student_token = await get_token_for(client, "student1@school1.org", "StudentPass123!")

    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

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
            "topics": ["Discriminant Analysis"],
            "question_count": 2,
            "total_marks": 5,
            "question_types": ["mcq", "short_answer"],
        },
        headers=teacher_headers,
    )
    assert gen_res.status_code == 202
    job_id = gen_res.json()["job_id"]

    # Poll job status
    poll_res = await client.get(f"/api/v1/generation/jobs/{job_id}", headers=teacher_headers)
    assert poll_res.status_code == 200
    asmt_id = poll_res.json()["assessment_id"]

    # 2. Teacher approves assessment
    appr_res = await client.post(
        f"/api/v1/assessments/{asmt_id}/approve",
        headers=teacher_headers,
    )
    assert appr_res.status_code == 200

    # 3. Teacher publishes assessment
    pub_res = await client.post(
        f"/api/v1/assessments/{asmt_id}/publish",
        json={
            "starts_at": "2026-11-01T00:00:00Z",
            "ends_at": "2026-11-30T23:59:59Z",
            "duration_minutes": 60,
            "max_attempts": 1,
            "result_release_mode": "manual_by_teacher",
        },
        headers=teacher_headers,
    )
    assert pub_res.status_code == 200

    # 4. Student starts attempt
    start_res = await client.post(
        f"/api/v1/assessments/{asmt_id}/attempts",
        headers=student_headers,
    )
    assert start_res.status_code == 201
    attempt_data = start_res.json()
    attempt_id = attempt_data["attempt_id"]
    questions = attempt_data["questions"]
    assert len(questions) == 2

    # Autosave response for first item
    save_res = await client.put(
        f"/api/v1/attempts/{attempt_id}/responses/{questions[0]['item_id']}",
        json={"answer_json": {"selected_option": "A"}},
        headers=student_headers,
    )
    assert save_res.status_code == 200

    # Submit attempt
    sub_res = await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers=student_headers,
    )
    assert sub_res.status_code == 200

    # 5. Test Assessment Analytics
    ana_res = await client.get(
        f"/api/v1/analytics/assessments/{asmt_id}",
        headers=teacher_headers,
    )
    assert ana_res.status_code == 200
    ana_data = ana_res.json()
    assert ana_data["assessment_id"] == asmt_id
    assert ana_data["submitted_count"] == 1
    assert "score_distribution" in ana_data
    assert len(ana_data["question_analysis"]) == 2
    for q_analysis in ana_data["question_analysis"]:
        assert "discrimination_index" in q_analysis
        assert "interpretation" in q_analysis

    # 6. Test Class Analytics
    class_ana_res = await client.get(
        f"/api/v1/analytics/classes/{class_id}",
        headers=teacher_headers,
    )
    assert class_ana_res.status_code == 200
    class_data = class_ana_res.json()
    assert class_data["class_id"] == class_id
    assert class_data["total_assessments"] >= 1
    assert len(class_data["assessments"]) >= 1

    # 7. Test Teacher Dashboard Summary
    dash_res = await client.get(
        "/api/v1/teacher/dashboard-summary",
        headers=teacher_headers,
    )
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["assigned_classes_count"] >= 1
    assert dash_data["active_assessments_count"] >= 1

    # 8. Test Topic Mastery
    topic_res = await client.get(
        "/api/v1/analytics/topics",
        headers=teacher_headers,
    )
    assert topic_res.status_code == 200
    topic_data = topic_res.json()
    assert isinstance(topic_data, list)

    # 9. Test Export CSV
    csv_res = await client.get(
        f"/api/v1/assessments/{asmt_id}/export/csv",
        headers=teacher_headers,
    )
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    csv_text = csv_res.text
    assert "Student Name" in csv_text
    assert "Total Score" in csv_text

    # 10. Test Export Printable Paper (PDF view)
    pdf_res = await client.get(
        f"/api/v1/assessments/{asmt_id}/export/pdf",
        headers=teacher_headers,
    )
    assert pdf_res.status_code == 200
    assert "text/html" in pdf_res.headers["content-type"]
    assert "General Instructions" in pdf_res.text

    # 11. Security: Student CANNOT access teacher marking scheme in export
    leak_test = await client.get(
        f"/api/v1/assessments/{asmt_id}/export/pdf?include_marking_scheme=true",
        headers=student_headers,
    )
    assert leak_test.status_code == 403

    # 12. Security: Student CANNOT query analytics
    student_ana = await client.get(
        f"/api/v1/analytics/assessments/{asmt_id}",
        headers=student_headers,
    )
    assert student_ana.status_code == 403
