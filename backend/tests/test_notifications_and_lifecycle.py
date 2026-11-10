"""
Phase 5 Tests: Notifications Store, Delivery Telemetry & StateGraph AI Studio Pipeline
"""
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.identity.models import User
from backend.app.assessments.models import Assessment
from backend.app.assessments.lifecycle_service import approve_assessment, publish_or_schedule_assessment
from backend.app.notifications.models import Notification
from backend.app.notifications.service import create_notification, EmailAdapter
from ai_engine.schemas.question import GenerationRequestSpec
from backend.app.generation.graph import run_generation_pipeline


async def login_user(client: AsyncClient, email: str, password: str) -> None:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_notification_creation_and_unread_count(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies in-app notification creation, unread count badge, and list retrieval."""
    student = seeded_test_data["student1"]
    school = seeded_test_data["school1"]

    # 1. Create notification
    notif = await create_notification(
        db=db_session,
        school_id=school.id,
        user_id=student.id,
        title="Welcome to Mind LMS",
        message="Your academic profile is ready.",
        type="system",
        channel="in_app",
    )
    assert notif.id is not None
    assert notif.is_read is False

    # 2. Login as student and check unread count
    await login_user(client, student.email, "StudentPass123!")
    res_count = await client.get("/api/v1/notifications/unread-count")
    assert res_count.status_code == 200
    assert res_count.json()["unread_count"] == 1

    # 3. Retrieve notifications list
    res_list = await client.get("/api/v1/notifications")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 1
    assert items[0]["title"] == "Welcome to Mind LMS"
    assert items[0]["is_read"] is False


@pytest.mark.asyncio
async def test_notification_mark_read_and_mark_all(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies marking single notification as read and bulk marking all as read."""
    student = seeded_test_data["student1"]
    school = seeded_test_data["school1"]

    n1 = await create_notification(
        db=db_session,
        school_id=school.id,
        user_id=student.id,
        title="Notice 1",
        message="Important reminder",
    )
    n2 = await create_notification(
        db=db_session,
        school_id=school.id,
        user_id=student.id,
        title="Notice 2",
        message="Calendar update",
    )

    await login_user(client, student.email, "StudentPass123!")

    # Mark n1 as read
    res_read = await client.patch(f"/api/v1/notifications/{n1.id}/read")
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # Count should now be 1
    res_c1 = await client.get("/api/v1/notifications/unread-count")
    assert res_c1.json()["unread_count"] == 1

    # Mark all read
    res_all = await client.post("/api/v1/notifications/mark-all-read")
    assert res_all.status_code == 200
    assert res_all.json()["marked_count"] >= 1

    # Count should now be 0
    res_c0 = await client.get("/api/v1/notifications/unread-count")
    assert res_c0.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_publishing_dispatches_notification_to_enrolled_students(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Publishing an assessment automatically sends in-app notifications to all enrolled students."""
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Teacher generates and approves an assessment
    await login_user(client, teacher.email, "TeacherPass123!")
    res_gen = await client.post(
        "/api/v1/generation/quizzes",
        json={
            "subject_id": sub_math.id,
            "class_id": class_11.id,
            "section_id": sec_11e.id,
            "chapter": "Differential Equations",
            "topics": ["Order and Degree"],
            "question_types": ["mcq"],
            "question_count": 2,
            "total_marks": 4,
            "difficulty": {"easy": 50, "medium": 50, "hard": 0},
        },
    )
    assert res_gen.status_code == 202

    # Fetch assessment
    stmt = select(Assessment).where(
        Assessment.class_id == class_11.id,
        Assessment.section_id == sec_11e.id,
    )
    asmt = (await db_session.execute(stmt)).scalars().first()
    assert asmt is not None

    # Approve assessment
    await client.post(f"/api/v1/assessments/{asmt.id}/approve")

    # Publish assessment
    now = datetime.now(timezone.utc)
    res_pub = await client.post(
        f"/api/v1/assessments/{asmt.id}/publish",
        json={
            "starts_at": now.isoformat(),
            "ends_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "Asia/Kolkata",
            "max_attempts": 1,
            "result_release_mode": "manual_by_teacher",
        },
    )
    assert res_pub.status_code == 200

    # 2. Student logs in and checks notifications
    await login_user(client, student.email, "StudentPass123!")
    res_notif = await client.get("/api/v1/notifications")
    assert res_notif.status_code == 200
    notifications = res_notif.json()
    assert any(
        n["type"] == "assignment_published" and asmt.title in n["title"]
        for n in notifications
    )


@pytest.mark.asyncio
async def test_submission_and_results_release_notification_flow(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Student submission notifies teacher; teacher result release notifies students."""
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Setup published assessment
    await login_user(client, teacher.email, "TeacherPass123!")
    res_gen = await client.post(
        "/api/v1/generation/quizzes",
        json={
            "subject_id": sub_math.id,
            "class_id": class_11.id,
            "section_id": sec_11e.id,
            "chapter": "Probability",
            "topics": ["Bayes Theorem"],
            "question_types": ["mcq"],
            "question_count": 2,
            "total_marks": 2,
            "difficulty": {"easy": 50, "medium": 50, "hard": 0},
        },
    )
    assert res_gen.status_code == 202

    stmt = select(Assessment).where(Assessment.title.contains("Probability"))
    asmt = (await db_session.execute(stmt)).scalars().first()
    await client.post(f"/api/v1/assessments/{asmt.id}/approve")

    now = datetime.now(timezone.utc)
    await client.post(
        f"/api/v1/assessments/{asmt.id}/publish",
        json={
            "starts_at": now.isoformat(),
            "ends_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "Asia/Kolkata",
            "max_attempts": 1,
            "result_release_mode": "manual_by_teacher",
        },
    )

    # 2. Student starts and submits attempt
    await login_user(client, student.email, "StudentPass123!")
    res_attempt = await client.post(f"/api/v1/assessments/{asmt.id}/attempts")
    assert res_attempt.status_code == 201
    attempt_id = res_attempt.json()["attempt_id"]

    res_submit = await client.post(f"/api/v1/attempts/{attempt_id}/submit")
    assert res_submit.status_code == 200

    # 3. Teacher logs in and checks for submission notification
    await login_user(client, teacher.email, "TeacherPass123!")
    res_t_notif = await client.get("/api/v1/notifications")
    assert res_t_notif.status_code == 200
    t_notifs = res_t_notif.json()
    assert any(n["type"] == "submission_received" for n in t_notifs)

    # 4. Teacher releases results
    res_rel = await client.post(f"/api/v1/assessments/{asmt.id}/release-results")
    assert res_rel.status_code == 200

    # 5. Student checks for results_released notification
    await login_user(client, student.email, "StudentPass123!")
    res_s_notif = await client.get("/api/v1/notifications")
    s_notifs = res_s_notif.json()
    assert any(n["type"] == "results_released" for n in s_notifs)


@pytest.mark.asyncio
async def test_ai_studio_stategraph_pipeline_and_trace(seeded_test_data: dict):
    """Agent Track A2: Verifies multi-node StateGraph execution with difficulty calibration."""
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    spec = GenerationRequestSpec(
        output_type="quiz",
        subject_id=sub_math.id,
        class_id=class_11.id,
        section_id=sec_11e.id,
        chapter="Matrices",
        topics=["Inverses and Determinants"],
        question_types=["mcq", "short_answer"],
        question_count=5,
        total_marks=10,
        difficulty_distribution={"easy": 40, "medium": 40, "hard": 20},
    )

    questions, warnings, trace = await run_generation_pipeline(spec=spec, prompt_version="v1.0")

    # 1. Output assertions
    assert len(questions) == 5
    assert sum(q.marks for q in questions) == 10

    # 2. StateGraph execution trace assertions
    node_names = [step["node"] for step in trace]
    assert "DraftGeneratorNode" in node_names
    assert "DifficultyTaggerNode" in node_names
    assert "MathAndIntegrityNode" in node_names

    # 3. Difficulty calibration check
    difficulties = [q.difficulty for q in questions]
    assert "easy" in difficulties
    assert "hard" in difficulties


@pytest.mark.asyncio
async def test_email_adapter_dispatch():
    """Verifies that EmailAdapter formats and logs dispatches reliably."""
    res = await EmailAdapter.send_email(
        to_email="principal@mind.school",
        subject="Weekly Academic Round-up",
        body_text="All weekly assessments have been published.",
    )
    assert res is True
