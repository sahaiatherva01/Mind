"""
Phase 4 Tests: Materials Management, Scoped Section Distribution, Open Tracking & Question Extractor Agent
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.identity.models import User
from backend.app.content.models import Material, MaterialDistribution, MaterialEngagement, Question


async def login_user(client: AsyncClient, email: str, password: str) -> None:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_teacher_upload_and_distribute_assigned_sections(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Teacher uploads material and distributes strictly to their assigned sections."""
    teacher = seeded_test_data["teacher1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    await login_user(client, teacher.email, "TeacherPass123!")

    payload = {
        "title": "Calculus Fundamentals Chapter 1",
        "description": "Comprehensive guide to limits and derivatives",
        "file_url": "https://storage.mind.local/springfield/calculus_ch1.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 1048576,
        "subject_id": sub_math.id,
        "class_id": class_11.id,
        "chapter": "Limits and Continuity",
        "topic": "Evaluation of Limits",
        "content_text": "Definition: A limit is defined as the value that a function approaches as the input approaches some value. The derivative measures the sensitivity to change of a function value with respect to a change in its argument.",
        "target_section_ids": [sec_11e.id],
    }

    res = await client.post("/api/v1/content/materials", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["distributed_section_ids"] == [sec_11e.id]
    assert data["open_count"] == 0

    # Verify database state
    mat_stmt = select(Material).where(Material.id == data["id"])
    mat = (await db_session.execute(mat_stmt)).scalar_one_or_none()
    assert mat is not None
    assert mat.uploader_id == teacher.id

    dist_stmt = select(MaterialDistribution).where(MaterialDistribution.material_id == mat.id)
    dists = (await db_session.execute(dist_stmt)).scalars().all()
    assert len(dists) == 1
    assert dists[0].section_id == sec_11e.id


@pytest.mark.asyncio
async def test_teacher_cannot_distribute_to_unassigned_section(
    client: AsyncClient, seeded_test_data: dict
):
    """Teacher attempting to share materials with a section they don't teach is blocked with 403 Forbidden."""
    teacher = seeded_test_data["teacher1"]
    class_12 = seeded_test_data["class_12"]
    sec_12d = seeded_test_data["sec_12d"]  # Teacher is NOT assigned to 12D
    sub_math = seeded_test_data["sub_math"]

    await login_user(client, teacher.email, "TeacherPass123!")

    payload = {
        "title": "Unauthorized Vectors Notes",
        "file_url": "https://storage.mind.local/springfield/vectors.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 500000,
        "subject_id": sub_math.id,
        "class_id": class_12.id,
        "chapter": "3D Vectors",
        "target_section_ids": [sec_12d.id],  # Illegal target section
    }

    res = await client.post("/api/v1/content/materials", json=payload)
    assert res.status_code == 403
    err_msg = res.json()["error"]["message"]
    assert "not assigned to teach section" in err_msg


@pytest.mark.asyncio
async def test_student_views_only_assigned_section_materials(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Student strictly sees only materials shared to sections they are enrolled in."""
    teacher = seeded_test_data["teacher1"]
    admin = seeded_test_data["admin1"]
    student = seeded_test_data["student1"]
    class_11 = seeded_test_data["class_11"]
    class_12 = seeded_test_data["class_12"]
    sec_11e = seeded_test_data["sec_11e"]  # Student 1 enrolled here
    sec_12d = seeded_test_data["sec_12d"]  # Student 1 NOT enrolled here
    sub_math = seeded_test_data["sub_math"]

    # 1. Teacher creates Material A for 11E
    await login_user(client, teacher.email, "TeacherPass123!")
    res_a = await client.post("/api/v1/content/materials", json={
        "title": "Algebra Sheet 11E",
        "file_url": "https://storage.mind.local/algebra_11e.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 10000,
        "subject_id": sub_math.id,
        "class_id": class_11.id,
        "chapter": "Algebra",
        "target_section_ids": [sec_11e.id],
    })
    assert res_a.status_code == 201
    mat_a_id = res_a.json()["id"]

    # 2. Admin creates Material B for 12D (not student's section)
    await login_user(client, admin.email, "AdminPass123!")
    res_b = await client.post("/api/v1/content/materials", json={
        "title": "Geometry Sheet 12D",
        "file_url": "https://storage.mind.local/geom_12d.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 20000,
        "subject_id": sub_math.id,
        "class_id": class_12.id,
        "chapter": "Geometry",
        "target_section_ids": [sec_12d.id],
    })
    assert res_b.status_code == 201
    mat_b_id = res_b.json()["id"]

    # 3. Student logs in and fetches My Learning
    await login_user(client, student.email, "StudentPass123!")
    res_student = await client.get("/api/v1/student/my-learning")
    assert res_student.status_code == 200
    materials = res_student.json()

    returned_ids = [m["id"] for m in materials]
    assert mat_a_id in returned_ids
    assert mat_b_id not in returned_ids  # Material B is NOT visible!


@pytest.mark.asyncio
async def test_student_open_event_tracking(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Student open events are tracked and update read telemetry."""
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Teacher creates material
    await login_user(client, teacher.email, "TeacherPass123!")
    res_mat = await client.post("/api/v1/content/materials", json={
        "title": "Reading Engagement Test",
        "file_url": "https://storage.mind.local/engagement.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 15000,
        "subject_id": sub_math.id,
        "class_id": class_11.id,
        "target_section_ids": [sec_11e.id],
    })
    mat_id = res_mat.json()["id"]

    # 2. Student views My Learning (has_opened should be False)
    await login_user(client, student.email, "StudentPass123!")
    res_before = await client.get("/api/v1/student/my-learning")
    item_before = next(m for m in res_before.json() if m["id"] == mat_id)
    assert item_before["has_opened"] is False
    assert item_before["last_opened_at"] is None

    # 3. Student opens material
    res_open = await client.post(
        f"/api/v1/student/my-learning/{mat_id}/open",
        json={"duration_seconds": 240, "pages_read": 8},
    )
    assert res_open.status_code == 200
    assert res_open.json()["status"] == "tracked"
    assert res_open.json()["duration_seconds"] == 240

    # 4. Student re-checks My Learning (has_opened is now True)
    res_after = await client.get("/api/v1/student/my-learning")
    item_after = next(m for m in res_after.json() if m["id"] == mat_id)
    assert item_after["has_opened"] is True
    assert item_after["last_opened_at"] is not None

    # 5. Teacher checks material detail and sees reader counts
    await login_user(client, teacher.email, "TeacherPass123!")
    res_detail = await client.get(f"/api/v1/content/materials/{mat_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["open_count"] == 1
    assert res_detail.json()["unique_readers_count"] == 1


@pytest.mark.asyncio
async def test_student_cannot_open_undistributed_material(
    client: AsyncClient, seeded_test_data: dict
):
    """Student cannot record open events for materials not distributed to their section."""
    admin = seeded_test_data["admin1"]
    student = seeded_test_data["student1"]
    class_12 = seeded_test_data["class_12"]
    sec_12d = seeded_test_data["sec_12d"]
    sub_math = seeded_test_data["sub_math"]

    # Admin creates material for 12D only
    await login_user(client, admin.email, "AdminPass123!")
    res_mat = await client.post("/api/v1/content/materials", json={
        "title": "Private Section Material",
        "file_url": "https://storage.mind.local/private.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 10000,
        "subject_id": sub_math.id,
        "class_id": class_12.id,
        "target_section_ids": [sec_12d.id],
    })
    mat_id = res_mat.json()["id"]

    # Student 1 (enrolled in 11E, not 12D) attempts to open it
    await login_user(client, student.email, "StudentPass123!")
    res_open = await client.post(f"/api/v1/student/my-learning/{mat_id}/open", json={})
    assert res_open.status_code == 403
    err_msg = res_open.json()["error"]["message"]
    assert "not enrolled in any section with access" in err_msg


@pytest.mark.asyncio
async def test_question_extractor_pipeline_and_review_gate(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """
    Question Extractor generates draft candidate questions in 'needs_review' state.
    Human teacher must explicitly review and approve them before they enter the Question Bank.
    """
    teacher = seeded_test_data["teacher1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    await login_user(client, teacher.email, "TeacherPass123!")

    # 1. Create material with structured academic text
    res_mat = await client.post("/api/v1/content/materials", json={
        "title": "Newton Laws of Motion Chapter Extract",
        "file_url": "https://storage.mind.local/physics_laws.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 45000,
        "subject_id": sub_math.id,
        "class_id": class_11.id,
        "chapter": "Laws of Motion",
        "content_text": """
SECTION 1: FIRST LAW OF MOTION
Inertia is defined as the inherent property of an object by which it resists any change in its state of rest or uniform motion in a straight line.
According to Galileo, a body in motion continues to move with constant velocity unless acted upon by an external net force.

SECTION 2: SECOND LAW OF MOTION
Force is defined as the rate of change of momentum with respect to time. The SI unit of force is the Newton.
F = ma governs the acceleration produced when a net unbalanced force acts on an object of mass m.
""",
        "target_section_ids": [sec_11e.id],
    })
    mat_id = res_mat.json()["id"]

    # 2. Trigger Question Extraction Agent
    res_extract = await client.post(
        f"/api/v1/content/materials/{mat_id}/extract-questions",
        json={"max_questions": 5},
    )
    assert res_extract.status_code == 200
    extract_data = res_extract.json()
    assert extract_data["status"] == "succeeded"
    assert extract_data["extracted_count"] > 0
    questions = extract_data["questions"]

    # Verify that EVERY extracted item starts in 'needs_review' state (human review gate)
    for q in questions:
        assert q["status"] == "needs_review"
        assert q["prompt"]
        assert q["expected_answer"]

    candidate = questions[0]

    # 3. Teacher accepts/approves the candidate question into the Question Bank
    res_approve = await client.post(
        f"/api/v1/content/materials/{mat_id}/approve-question",
        json={
            "candidate_question_id": candidate["id"],
            "prompt": candidate["prompt"],
            "category": candidate["category"],
            "type": candidate["type"],
            "marks": candidate["marks"],
            "difficulty": candidate["difficulty"],
            "expected_answer": candidate["expected_answer"],
            "marking_scheme": candidate["marking_scheme"],
            "options": candidate.get("options"),
            "answer_keys": candidate.get("answer_keys"),
        },
    )
    assert res_approve.status_code == 201
    approve_data = res_approve.json()
    assert approve_data["status"] == "approved"
    assert "question_id" in approve_data

    # 4. Verify canonical Question in database is marked active
    q_stmt = select(Question).where(Question.id == approve_data["question_id"])
    canonical_q = (await db_session.execute(q_stmt)).scalar_one_or_none()
    assert canonical_q is not None
    assert canonical_q.status == "active"
    assert canonical_q.prompt == candidate["prompt"]


@pytest.mark.asyncio
async def test_delete_material_and_archival(
    client: AsyncClient, seeded_test_data: dict, db_session: AsyncSession
):
    """Archiving material prevents students from viewing or accessing it."""
    teacher = seeded_test_data["teacher1"]
    student = seeded_test_data["student1"]
    class_11 = seeded_test_data["class_11"]
    sec_11e = seeded_test_data["sec_11e"]
    sub_math = seeded_test_data["sub_math"]

    # 1. Teacher creates material
    await login_user(client, teacher.email, "TeacherPass123!")
    res_mat = await client.post("/api/v1/content/materials", json={
        "title": "Ephemeral Notes to Archive",
        "file_url": "https://storage.mind.local/notes.pdf",
        "file_type": "application/pdf",
        "file_size_bytes": 5000,
        "subject_id": sub_math.id,
        "class_id": class_11.id,
        "target_section_ids": [sec_11e.id],
    })
    mat_id = res_mat.json()["id"]

    # 2. Student confirms it is visible
    await login_user(client, student.email, "StudentPass123!")
    res_student_1 = await client.get("/api/v1/student/my-learning")
    assert any(m["id"] == mat_id for m in res_student_1.json())

    # 3. Teacher deletes it
    await login_user(client, teacher.email, "TeacherPass123!")
    res_del = await client.delete(f"/api/v1/content/materials/{mat_id}")
    assert res_del.status_code == 204

    # 4. Student confirms it is no longer listed
    await login_user(client, student.email, "StudentPass123!")
    res_student_2 = await client.get("/api/v1/student/my-learning")
    assert not any(m["id"] == mat_id for m in res_student_2.json())
