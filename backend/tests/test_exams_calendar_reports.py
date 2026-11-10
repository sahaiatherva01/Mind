"""
Phase 7 Tests: Exams, Academic Calendar, Multi-Set Blueprints, Evaluation Assistant & Report Cards
"""
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.identity.models import User, RoleAssignment, RoleName
from backend.app.academics.models import Class, Section, Subject, TeacherAssignment, StudentEnrollment
from backend.app.assessments.models import (
    Assessment,
    AssessmentItem,
    Schedule,
    Attempt,
    StudentResponse,
    AssessmentStatus,
    AttemptStatus,
)
from backend.app.content.models import Question
from backend.app.exams.models import CalendarEvent, CalendarEventType, ExamBlueprint, ExamBlueprintStatus


async def login_user(client: AsyncClient, email: str, password: str) -> None:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_calendar_event_creation_and_listing(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies that School Admin can create calendar events while Students are denied."""
    admin = seeded_test_data["admin1"]
    student = seeded_test_data["student1"]
    school = seeded_test_data["school1"]

    await login_user(client, admin.email, "AdminPass123!")

    now = datetime.now(timezone.utc)
    event_payload = {
        "title": "Winter Term Exam Period",
        "event_type": "exam_period",
        "starts_at": (now + timedelta(days=5)).isoformat(),
        "ends_at": (now + timedelta(days=12)).isoformat(),
        "description": "Comprehensive term exams across all academic bands.",
    }

    res = await client.post("/api/v1/calendar/events", json=event_payload)
    assert res.status_code == 201
    created_event = res.json()
    assert created_event["title"] == "Winter Term Exam Period"
    assert created_event["school_id"] == school.id

    # List events
    res_list = await client.get("/api/v1/calendar/events")
    assert res_list.status_code == 200
    events = res_list.json()
    assert len(events) >= 1

    # Student cannot create events
    await login_user(client, student.email, "StudentPass123!")
    res_deny = await client.post("/api/v1/calendar/events", json=event_payload)
    assert res_deny.status_code == 403


@pytest.mark.asyncio
async def test_exam_clash_detection_and_policy_limits(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """
    Verifies calendar conflict detection:
    1. Blackout window violation.
    2. Policy Limit: Maximum 2 assessments/day per section.
    """
    admin = seeded_test_data["admin1"]
    teacher = seeded_test_data["teacher1"]
    school = seeded_test_data["school1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Create a blackout window on Day 10
    now = datetime.now(timezone.utc)
    day10_start = (now + timedelta(days=10)).replace(hour=0, minute=0, second=0)
    day10_end = (now + timedelta(days=10)).replace(hour=23, minute=59, second=59)

    blackout = CalendarEvent(
        school_id=school.id,
        title="Annual Sports Day (Blackout)",
        event_type=CalendarEventType.BLACKOUT,
        starts_at=day10_start,
        ends_at=day10_end,
        created_by=admin.id,
    )
    db_session.add(blackout)
    await db_session.flush()

    await login_user(client, teacher.email, "TeacherPass123!")

    # Check clash on blackout day
    res_blackout = await client.post(
        "/api/v1/calendar/check-clash",
        json={
            "section_id": sec_11e.id,
            "starts_at": (day10_start + timedelta(hours=10)).isoformat(),
            "ends_at": (day10_start + timedelta(hours=12)).isoformat(),
        },
    )
    assert res_blackout.status_code == 200
    data_b = res_blackout.json()
    assert data_b["has_clash"] is True
    assert data_b["clash_type"] == "blackout"
    assert "Annual Sports Day" in data_b["message"]

    # 2. Check Daily Limit: Schedule 2 assessments on Day 15 for 11E
    day15_slot1 = (now + timedelta(days=15)).replace(hour=9, minute=0, second=0)
    day15_slot2 = (now + timedelta(days=15)).replace(hour=14, minute=0, second=0)

    for i, slot in enumerate([day15_slot1, day15_slot2]):
        asmt = Assessment(
            school_id=school.id,
            creator_id=teacher.id,
            class_id=class_11.id,
            section_id=sec_11e.id,
            subject_id=sub_math.id,
            title=f"Math Test {i+1}",
            type="quiz",
            status=AssessmentStatus.PUBLISHED,
        )
        db_session.add(asmt)
        await db_session.flush()

        sched = Schedule(
            school_id=school.id,
            assessment_id=asmt.id,
            starts_at=slot,
            ends_at=slot + timedelta(hours=1),
        )
        db_session.add(sched)
    await db_session.flush()

    # Attempt to schedule a 3rd assessment on Day 15
    res_limit = await client.post(
        "/api/v1/calendar/check-clash",
        json={
            "section_id": sec_11e.id,
            "starts_at": (day15_slot1 + timedelta(hours=2)).isoformat(),
            "ends_at": (day15_slot1 + timedelta(hours=3)).isoformat(),
        },
    )
    assert res_limit.status_code == 200
    data_l = res_limit.json()
    assert data_l["has_clash"] is True
    assert data_l["clash_type"] == "policy_limit"
    assert "maximum limit of 2 assessments" in data_l["message"]


@pytest.mark.asyncio
async def test_band_exam_blueprint_and_multiset_generation(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """
    Verifies that Academic Coordinator can define an exam blueprint,
    generate parallel Sets A, B, C, D, and approve them.
    """
    coord = seeded_test_data["coord1"]
    teacher = seeded_test_data["teacher1"]
    band_senior = seeded_test_data["band_senior"]
    sub_math = seeded_test_data["sub_math"]

    await login_user(client, coord.email, "CoordPass123!")

    # 1. Create Blueprint
    bp_payload = {
        "band_id": band_senior.id,
        "subject_id": sub_math.id,
        "title": "Senior Term 1 Mathematics Board Exam",
        "total_marks": 80.0,
        "duration_minutes": 180,
        "term": "Term 1",
        "sections": [
            {"section_name": "Section A", "question_type": "mcq", "count": 10, "marks_per_question": 2.0},
            {"section_name": "Section B", "question_type": "short_answer", "count": 6, "marks_per_question": 5.0},
            {"section_name": "Section C", "question_type": "long_answer", "count": 3, "marks_per_question": 10.0},
        ],
        "topics": ["Matrices & Determinants", "Differential Calculus", "Probability Distribution"],
        "difficulty_ratio": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
    }

    res_create = await client.post("/api/v1/exams/blueprints", json=bp_payload)
    assert res_create.status_code == 201
    bp_data = res_create.json()
    bp_id = bp_data["id"]
    assert bp_data["status"] == "draft"

    # 2. Generate Sets A, B, C, D
    res_gen = await client.post(f"/api/v1/exams/blueprints/{bp_id}/generate-sets")
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["status"] == "generated"
    sets = gen_data["sets_data_json"]
    assert len(sets) == 4  # Set A, Set B, Set C, Set D
    assert sets[0]["set_label"] == "Set A"
    assert sets[1]["set_label"] == "Set B"
    assert sets[2]["set_label"] == "Set C"
    assert sets[3]["set_label"] == "Set D"
    assert sets[0]["total_marks"] == 80.0
    assert sets[1]["total_marks"] == 80.0

    # 3. Coordinator Approves Blueprint
    res_app = await client.post(f"/api/v1/exams/blueprints/{bp_id}/approve")
    assert res_app.status_code == 200
    app_data = res_app.json()
    assert app_data["status"] == "approved"
    assert app_data["approved_by"] == coord.id

    # 4. Teacher cannot approve blueprints (403 Forbidden)
    await login_user(client, teacher.email, "TeacherPass123!")
    res_t_deny = await client.post(f"/api/v1/exams/blueprints/{bp_id}/approve")
    assert res_t_deny.status_code == 403


@pytest.mark.asyncio
async def test_evaluation_assistant_agent_track_a3(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """
    Verifies Agent Track A3 (Subjective Evaluator Agent):
    - Analyzes student response against question rubric
    - Produces calibrated numerical score & step breakdown
    - Human-in-the-loop review gate verified
    """
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    school = seeded_test_data["school1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Seed assessment & question
    q = Question(
        school_id=school.id,
        subject_id=sub_math.id,
        type="short_answer",
        prompt="State Lagrange's Mean Value Theorem and explain its geometric interpretation.",
        marks=4.0,
        answer_data={
            "model_answer": "If f(x) is continuous on [a,b] and differentiable on (a,b), then there exists c in (a,b) where f'(c) = (f(b)-f(a))/(b-a). Geometrically, tangent is parallel to secant line.",
            "rubric_steps": [
                "Statement of continuity and differentiability conditions",
                "Mathematical formula for instantaneous rate of change",
                "Geometric interpretation: parallel tangent to secant chord",
            ],
        },
    )
    db_session.add(q)
    await db_session.flush()

    asmt = Assessment(
        school_id=school.id,
        creator_id=teacher.id,
        class_id=class_11.id,
        section_id=sec_11e.id,
        subject_id=sub_math.id,
        title="Calculus Theorems Term Exam",
        type="worksheet",
        status=AssessmentStatus.PUBLISHED,
    )
    db_session.add(asmt)
    await db_session.flush()

    item = AssessmentItem(
        assessment_id=asmt.id,
        question_id=q.id,
        position=1,
        marks_override=4.0,
    )
    db_session.add(item)
    await db_session.flush()

    attempt = Attempt(
        school_id=school.id,
        assessment_id=asmt.id,
        student_id=student.id,
        status=AttemptStatus.SUBMITTED,
        total_score=0.0,
        max_score=4.0,
    )
    db_session.add(attempt)
    await db_session.flush()

    resp = StudentResponse(
        attempt_id=attempt.id,
        assessment_item_id=item.id,
        answer_json={
            "text": "f(x) must be continuous and differentiable on interval. There exists point c where f'(c) = (f(b)-f(a))/(b-a). The tangent at c is parallel to the line joining the endpoints."
        },
    )
    db_session.add(resp)
    await db_session.flush()

    # 2. Teacher requests AI Evaluation Assistance
    await login_user(client, teacher.email, "TeacherPass123!")
    res_assist = await client.post(f"/api/v1/evaluations/{resp.id}/ai-assist")
    assert res_assist.status_code == 200
    data = res_assist.json()
    assert data["response_id"] == resp.id
    assert data["max_marks"] == 4.0
    assert 0.0 <= data["suggested_score"] <= 4.0
    assert len(data["step_breakdown"]) >= 2
    assert "teacher_feedback_note" in data
    assert data["confidence_score"] >= 0.70

    # 3. Human Review Gate: Teacher accepts/modifies and commits final grade
    res_grade = await client.patch(
        f"/api/v1/evaluations/{resp.id}",
        json={
            "manual_score": data["suggested_score"],
            "teacher_feedback": data["teacher_feedback_note"],
        },
    )
    assert res_grade.status_code == 200
    assert res_grade.json()["manual_score"] == data["suggested_score"]


@pytest.mark.asyncio
async def test_resilient_exam_player_telemetry(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies that exam player anti-cheat telemetry records tab switches and fullscreen departures."""
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    school = seeded_test_data["school1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    asmt = Assessment(
        school_id=school.id,
        creator_id=teacher.id,
        class_id=class_11.id,
        section_id=sec_11e.id,
        subject_id=sub_math.id,
        title="Proctored Final Exam",
        type="worksheet",
        status=AssessmentStatus.PUBLISHED,
    )
    db_session.add(asmt)
    await db_session.flush()

    attempt = Attempt(
        school_id=school.id,
        assessment_id=asmt.id,
        student_id=student.id,
        status=AttemptStatus.IN_PROGRESS,
    )
    db_session.add(attempt)
    await db_session.flush()

    await login_user(client, student.email, "StudentPass123!")

    # 1. Log tab switch
    res_tab = await client.post(
        f"/api/v1/attempts/{attempt.id}/telemetry",
        json={"event_type": "tab_switch", "details": {"active_window": "browser"}},
    )
    assert res_tab.status_code == 200
    assert res_tab.json()["tab_switches_count"] == 1

    # 2. Log fullscreen departure
    res_fs = await client.post(
        f"/api/v1/attempts/{attempt.id}/telemetry",
        json={"event_type": "fullscreen_exit", "details": {"reason": "escape_key"}},
    )
    assert res_fs.status_code == 200
    assert res_fs.json()["total_integrity_events"] == 2


@pytest.mark.asyncio
async def test_branded_report_card_and_gradebook(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies student report card generation and section gradebook matrix."""
    student = seeded_test_data["student1"]
    teacher = seeded_test_data["teacher1"]
    sec_11e = seeded_test_data["sec_11e"]

    # 1. Student views own report card
    await login_user(client, student.email, "StudentPass123!")
    res_rc = await client.get(f"/api/v1/reports/student/{student.id}/report-card")
    assert res_rc.status_code == 200
    rc = res_rc.json()
    assert rc["student_id"] == student.id
    assert rc["school_name"] is not None
    assert len(rc["subjects"]) >= 1
    assert "overall_grade" in rc
    assert "attendance_pct" in rc

    # 2. Teacher views section gradebook
    await login_user(client, teacher.email, "TeacherPass123!")
    res_gb = await client.get(f"/api/v1/reports/sections/{sec_11e.id}/gradebook")
    assert res_gb.status_code == 200
    gb = res_gb.json()
    assert gb["section_id"] == sec_11e.id
    assert len(gb["students"]) >= 1
    assert "section_average_pct" in gb
