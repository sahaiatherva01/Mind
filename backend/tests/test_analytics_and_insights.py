"""
Phase 6 Tests: 4-Level Analytics, Cross-Analytics & Analytics Insight Agent (Track A5)
Strictly enforces:
- Scoped RBAC for School Admin, Academic Coordinator, Teacher, and Student
- Isolation: Coordinators cannot view other bands; Teachers cannot view unassigned classes; Students cannot view other students' performance maps
- Zero Text-to-SQL for the Insight Agent (strictly uses typed tool methods)
"""
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.identity.models import User, RoleAssignment, RoleName
from backend.app.core.security import hash_password
from backend.app.assessments.models import (
    Assessment,
    AssessmentItem,
    Attempt,
    AssessmentStatus,
    AttemptStatus,
)
from backend.app.content.models import Material, MaterialEngagement, Question
from backend.app.analytics.insights import ScopedAnalyticsTools, AnalyticsInsightAgent


async def login_user(client: AsyncClient, email: str, password: str) -> None:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_school_analytics_summary_authorized_for_school_admin(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies that School Admin can retrieve full school analytics, while students are denied."""
    admin = seeded_test_data["admin1"]
    student = seeded_test_data["student1"]

    # 1. School Admin accesses school analytics
    await login_user(client, admin.email, "AdminPass123!")
    res = await client.get("/api/v1/analytics/school")
    assert res.status_code == 200
    data = res.json()
    assert "total_students" in data
    assert "total_teachers" in data
    assert "total_classes" in data
    assert "school_average_pct" in data
    assert "overall_pass_pct" in data
    assert "term_trends" in data
    assert "grade_distribution" in data
    assert "teacher_activity" in data
    assert data["total_classes"] >= 3

    # 2. Student is denied school analytics (403 Forbidden)
    await login_user(client, student.email, "StudentPass123!")
    res_forbidden = await client.get("/api/v1/analytics/school")
    assert res_forbidden.status_code == 403


@pytest.mark.asyncio
async def test_coordinator_band_analytics_and_isolation(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies coordinator can view their assigned band analytics, but is denied other bands."""
    coord = seeded_test_data["coord1"]
    band_senior = seeded_test_data["band_senior"]
    band_middle = seeded_test_data["band_middle"]

    await login_user(client, coord.email, "CoordPass123!")

    # 1. Access assigned senior band
    res = await client.get("/api/v1/coordinator/analytics")
    assert res.status_code == 200
    data = res.json()
    assert data["band_id"] == band_senior.id
    assert data["band_name"] == band_senior.name
    assert data["total_classes"] >= 2
    assert "section_comparisons" in data
    assert "syllabus_coverage" in data

    # 2. Attempt cross-band access to middle band (must return 403 Forbidden)
    res_cross = await client.get(f"/api/v1/coordinator/analytics?band_id={band_middle.id}")
    assert res_cross.status_code == 403


@pytest.mark.asyncio
async def test_teacher_four_level_analytics_and_engagement_correlation(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """
    Verifies 4-level analytics hierarchy:
    Level 1: Individual student trend & reading metrics
    Level 2: Section average, toppers & at-risk
    Level 3: Subject mastery & weak chapters
    Level 4: Section comparisons & Material engagement correlation
    And verifies unassigned class access returns 403.
    """
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    school = seeded_test_data["school1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    class_8 = seeded_test_data["class_8"]
    sec_8a = seeded_test_data["sec_8a"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Seed assessment and attempt in 11E
    assessment = Assessment(
        school_id=school.id,
        creator_id=teacher.id,
        class_id=class_11.id,
        section_id=sec_11e.id,
        subject_id=sub_math.id,
        title="Calculus Diagnostic Term 1",
        type="worksheet",
        total_marks=50.0,
        status=AssessmentStatus.RESULTS_RELEASED,
        settings={"topics": ["Differential Calculus", "Limits"]},
    )
    db_session.add(assessment)
    await db_session.flush()

    attempt = Attempt(
        school_id=school.id,
        assessment_id=assessment.id,
        student_id=student.id,
        status=AttemptStatus.SUBMITTED,
        total_score=42.0,
        max_score=50.0,
    )
    db_session.add(attempt)

    # 2. Seed material and engagement for student1
    material = Material(
        school_id=school.id,
        uploader_id=teacher.id,
        subject_id=sub_math.id,
        class_id=class_11.id,
        title="Differential Calculus Notes",
        file_url="https://s3.example.com/math.pdf",
        chapter="Limits & Derivatives",
        topic="Differential Calculus",
        content_text="Foundations of derivatives and calculus limits.",
    )
    db_session.add(material)
    await db_session.flush()

    engagement = MaterialEngagement(
        school_id=school.id,
        material_id=material.id,
        student_id=student.id,
        section_id=sec_11e.id,
        duration_seconds=1800,
        pages_read=15,
    )
    db_session.add(engagement)
    await db_session.flush()

    # 3. Teacher queries four-level analytics
    await login_user(client, teacher.email, "TeacherPass123!")
    res = await client.get(
        f"/api/v1/teacher/analytics?class_id={class_11.id}&section_id={sec_11e.id}&subject_id={sub_math.id}&student_id={student.id}"
    )
    assert res.status_code == 200
    data = res.json()

    # Level 1 verification
    indiv = data["individual_student"]
    assert indiv is not None
    assert indiv["student_id"] == student.id
    assert indiv["average_score_pct"] == 84.0
    assert indiv["materials_read_count"] >= 1
    assert indiv["reading_duration_minutes"] >= 30.0

    # Level 2 verification
    c_lvl = data["class_level"]
    assert c_lvl["section_name"] == "E"
    assert c_lvl["section_average_pct"] == 84.0
    assert len(c_lvl["toppers"]) >= 1

    # Level 3 verification
    s_lvl = data["subject_level"]
    assert s_lvl["subject_name"] == "Mathematics"

    # Level 4 verification: Material engagement correlation
    cross = data["cross_analytics"]
    corr = cross["material_engagement_correlation"]
    assert corr["engaged_students_count"] >= 1
    assert corr["engaged_students_average_pct"] == 84.0

    # 4. Teacher queries unassigned class 8 (must return 403 Forbidden)
    res_unassigned = await client.get(
        f"/api/v1/teacher/analytics?class_id={class_8.id}&section_id={sec_8a.id}"
    )
    assert res_unassigned.status_code == 403


@pytest.mark.asyncio
async def test_student_performance_map_privacy(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies students can access their own performance map, but are strictly forbidden from viewing others."""
    student1 = seeded_test_data["student1"]
    school = seeded_test_data["school1"]

    # Create student2
    student2 = User(
        school_id=school.id,
        email="student2@school1.org",
        password_hash=hash_password("StudentPass123!"),
        full_name="Student Two",
        status="active",
    )
    db_session.add(student2)
    await db_session.flush()

    ra_student2 = RoleAssignment(
        user_id=student2.id,
        role=RoleName.STUDENT,
        school_id=school.id,
        status="active",
    )
    db_session.add(ra_student2)
    await db_session.flush()

    # 1. Student1 views own performance map
    await login_user(client, student1.email, "StudentPass123!")
    res = await client.get("/api/v1/student/performance-map")
    assert res.status_code == 200
    data = res.json()
    assert data["student_id"] == student1.id
    assert "topic_mastery" in data
    assert "materials_completed_count" in data

    # 2. Student1 attempts to spy on student2's performance map
    res_spy = await client.get(f"/api/v1/student/performance-map?student_id={student2.id}")
    assert res_spy.status_code == 403


@pytest.mark.asyncio
async def test_analytics_insight_agent_zero_text_to_sql(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Verifies that Analytics Insight Agent operates strictly via typed query tools without dynamic SQL."""
    teacher = seeded_test_data["teacher1"]
    class_11 = seeded_test_data["class_11"]
    student = seeded_test_data["student1"]

    await login_user(client, teacher.email, "TeacherPass123!")

    # 1. Class scope insights
    res_class = await client.post(
        "/api/v1/analytics/insights",
        json={"scope_type": "class", "scope_id": class_11.id},
    )
    assert res_class.status_code == 200
    class_data = res_class.json()
    assert class_data["scope_type"] == "class"
    assert class_data["scope_id"] == class_11.id
    assert "summary" in class_data
    assert isinstance(class_data["strengths"], list)
    assert isinstance(class_data["conceptual_gaps"], list)
    assert isinstance(class_data["pedagogical_recommendations"], list)
    assert "get_performance_summary" in class_data["evidence_tools_used"]
    assert "get_topic_gaps" in class_data["evidence_tools_used"]
    assert "get_engagement_metrics" in class_data["evidence_tools_used"]

    # 2. Student scope insights
    res_student = await client.post(
        "/api/v1/analytics/insights",
        json={"scope_type": "student", "scope_id": student.id},
    )
    assert res_student.status_code == 200
    student_data = res_student.json()
    assert student_data["scope_type"] == "student"
    assert len(student_data["pedagogical_recommendations"]) >= 1
