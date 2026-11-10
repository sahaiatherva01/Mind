"""
Phase 8 Tests: Advanced Non-Parked Workflows
Includes:
- Early-Warning Signals & Coordinator Interventions
- Smart Student Groups & One-Click Remedial Generation (with human review gate)
- Substitute Teacher Management with Automated Temporal Access Revocation
- Student Academic Goals, Revision List & Structured Doubts
"""
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.identity.models import User, RoleAssignment, RoleName
from backend.app.core.security import hash_password
from backend.app.academics.models import Class, Section, Subject, TeacherAssignment, StudentEnrollment
from backend.app.assessments.models import (
    Assessment,
    AssessmentItem,
    Attempt,
    StudentResponse,
    AssessmentStatus,
    AttemptStatus,
)
from backend.app.content.models import Question
from backend.app.workflows.models import CoordinatorIntervention, SmartStudentGroup


async def login_user(client: AsyncClient, email: str, password: str) -> None:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_early_warning_signals_and_interventions(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies that early-warning signals flag at-risk students and coordinators can track interventions."""
    coord = seeded_test_data["coord1"]
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    school = seeded_test_data["school1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]
    band_senior = seeded_test_data["band_senior"]

    # 1. Seed two poor consecutive attempts (<45%)
    for i in range(2):
        asmt = Assessment(
            school_id=school.id,
            creator_id=teacher.id,
            class_id=class_11.id,
            section_id=sec_11e.id,
            subject_id=sub_math.id,
            title=f"Diagnostic Quiz #{i+1}",
            type="quiz",
            status=AssessmentStatus.RESULTS_RELEASED,
        )
        db_session.add(asmt)
        await db_session.flush()

        att = Attempt(
            school_id=school.id,
            assessment_id=asmt.id,
            student_id=student.id,
            status=AttemptStatus.SUBMITTED,
            total_score=15.0 if i == 0 else 10.0,  # Declining trajectory
            max_score=50.0,
        )
        db_session.add(att)
    await db_session.flush()

    # 2. Coordinator retrieves early warning signals
    await login_user(client, coord.email, "CoordPass123!")
    res_signals = await client.get("/api/v1/coordinator/early-warnings")
    assert res_signals.status_code == 200
    signals = res_signals.json()
    assert len(signals) >= 1
    target_sig = next(s for s in signals if s["student_id"] == student.id)
    assert target_sig["severity"] in ("high", "critical")
    assert len(target_sig["risk_factors"]) >= 1

    # 3. Coordinator logs intervention
    payload = {
        "band_id": band_senior.id,
        "student_id": student.id,
        "trigger_reason": "Low cumulative marks (25%) and negative score progression.",
        "severity": "high",
        "notes": "Parent-teacher conference requested; remedial worksheets assigned.",
    }
    res_inter = await client.post("/api/v1/coordinator/interventions", json=payload)
    assert res_inter.status_code == 201
    inter_data = res_inter.json()
    inter_id = inter_data["id"]
    assert inter_data["status"] == "open"

    # 4. Coordinator updates intervention to resolved
    res_patch = await client.patch(
        f"/api/v1/coordinator/interventions/{inter_id}",
        json={
            "status": "resolved",
            "action_taken": "Conducted 1-on-1 tutoring sessions and verified retention.",
        },
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_smart_student_groups_and_remedial_generation(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies teacher smart group segmentation and one-click remedial generation with human review gate."""
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    await login_user(client, teacher.email, "TeacherPass123!")

    # 1. Create Smart Group
    group_payload = {
        "class_id": class_11.id,
        "section_id": sec_11e.id,
        "subject_id": sub_math.id,
        "name": "Calculus Remedial Cohort",
        "group_type": "remedial",
        "student_ids": [student.id],
        "weak_topics": ["Limits", "Derivatives", "Mean Value Theorem"],
    }
    res_create = await client.post("/api/v1/teacher/smart-groups", json=group_payload)
    assert res_create.status_code == 201
    group_data = res_create.json()
    group_id = group_data["id"]

    # 2. Trigger One-Click Remedial Generation
    res_gen = await client.post(f"/api/v1/teacher/smart-groups/{group_id}/generate-remedial")
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["group_id"] == group_id
    assert gen_data["status"] == "needs_review"  # Human review gate mandatory!
    assert gen_data["questions_count"] == 4
    assert len(gen_data["weak_topics"]) >= 1


@pytest.mark.asyncio
async def test_substitute_teacher_temporal_access_revocation(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """
    Verifies temporal authorization revocation:
    - Substitute teacher has access strictly within (valid_from <= now <= valid_to)
    - Expired substitution immediately results in 403 Forbidden!
    """
    coord = seeded_test_data["coord1"]
    school = seeded_test_data["school1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Create substitute teacher user
    sub_teacher = User(
        school_id=school.id,
        email="substitute.teacher@school1.org",
        password_hash=hash_password("SubPass123!"),
        full_name="Substitute Teacher",
        status="active",
    )
    db_session.add(sub_teacher)
    await db_session.flush()

    ra_sub = RoleAssignment(
        user_id=sub_teacher.id,
        role=RoleName.TEACHER,
        school_id=school.id,
        status="active",
    )
    db_session.add(ra_sub)
    await db_session.flush()

    # 2. Coordinator assigns substitute with EXPIRED date window (5 days ago to 1 day ago)
    now = datetime.now(timezone.utc)
    expired_payload = {
        "teacher_id": sub_teacher.id,
        "class_id": class_11.id,
        "section_id": sec_11e.id,
        "subject_id": sub_math.id,
        "valid_from": (now - timedelta(days=5)).isoformat(),
        "valid_to": (now - timedelta(days=1)).isoformat(),
        "reason": "Teacher medical leave cover",
    }

    await login_user(client, coord.email, "CoordPass123!")
    res_asgn = await client.post("/api/v1/coordinator/substitutions", json=expired_payload)
    assert res_asgn.status_code == 201

    # 3. Substitute teacher attempts action on 11E -> MUST BE FORBIDDEN (403) due to temporal revocation!
    await login_user(client, sub_teacher.email, "SubPass123!")
    res_denied = await client.get(
        f"/api/v1/teacher/analytics?class_id={class_11.id}&section_id={sec_11e.id}"
    )
    assert res_denied.status_code == 403

    # 4. Coordinator updates substitute to VALID active date window
    active_payload = {
        "teacher_id": sub_teacher.id,
        "class_id": class_11.id,
        "section_id": sec_11e.id,
        "subject_id": sub_math.id,
        "valid_from": (now - timedelta(hours=1)).isoformat(),
        "valid_to": (now + timedelta(days=2)).isoformat(),
        "reason": "Active substitution",
    }
    await login_user(client, coord.email, "CoordPass123!")
    res_active = await client.post("/api/v1/coordinator/substitutions", json=active_payload)
    assert res_active.status_code == 201

    # 5. Substitute teacher attempts action -> NOW ALLOWED (200 OK)!
    await login_user(client, sub_teacher.email, "SubPass123!")
    res_allowed = await client.get(
        f"/api/v1/teacher/analytics?class_id={class_11.id}&section_id={sec_11e.id}"
    )
    assert res_allowed.status_code == 200


@pytest.mark.asyncio
async def test_student_goals_revision_list_and_doubts(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies student academic goals, smart revision list, and teacher doubt resolution."""
    student = seeded_test_data["student1"]
    teacher = seeded_test_data["teacher1"]
    sub_math = seeded_test_data["sub_math"]
    school = seeded_test_data["school1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]

    # 1. Student sets target goal
    await login_user(client, student.email, "StudentPass123!")
    res_goal = await client.post(
        "/api/v1/student/goals",
        json={"subject_id": sub_math.id, "target_score_pct": 88.0, "notes": "Target for Term 1 Final"},
    )
    assert res_goal.status_code == 201
    g_data = res_goal.json()
    assert g_data["target_score_pct"] == 88.0

    # 2. Student retrieves goals list
    res_g_list = await client.get("/api/v1/student/goals")
    assert res_g_list.status_code == 200
    assert len(res_g_list.json()) >= 1

    # 3. Student retrieves smart revision list
    res_rev = await client.get("/api/v1/student/revision-list")
    assert res_rev.status_code == 200
    assert isinstance(res_rev.json(), list)

    # 4. Student submits academic doubt
    res_doubt = await client.post(
        "/api/v1/student/doubts",
        json={
            "subject_id": sub_math.id,
            "query_text": "Could you please explain why Rolle's theorem requires differentiability on the open interval rather than the closed interval?",
        },
    )
    assert res_doubt.status_code == 201
    d_data = res_doubt.json()
    doubt_id = d_data["id"]
    assert d_data["status"] == "pending"

    # 5. Teacher answers student doubt
    await login_user(client, teacher.email, "TeacherPass123!")
    res_ans = await client.patch(
        f"/api/v1/teacher/doubts/{doubt_id}/answer",
        json={
            "response_text": "Because the derivative at the endpoints may not exist in a bilateral sense; only continuity at endpoints is required for the extreme value theorem to guarantee an interior extremum."
        },
    )
    assert res_ans.status_code == 200
    ans_data = res_ans.json()
    assert ans_data["status"] == "answered"
    assert ans_data["response_text"] is not None
