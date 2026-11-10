"""
Content Service: Learning Materials Management, Scoped Distribution, Open Tracking & Question Extractor
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import ForbiddenException, NotFoundException, ValidationException
from backend.app.core.policies import authorize
from backend.app.core.permission_matrix import Action
from backend.app.identity.models import User, RoleName
from backend.app.academics.models import Class, Section, Subject, TeacherAssignment, StudentEnrollment
from backend.app.content.models import Material, MaterialDistribution, MaterialEngagement, QuestionExtractionJob, Question
from backend.app.content.schemas import (
    MaterialCreate,
    MaterialOut,
    StudentMaterialOut,
    QuestionApprovalRequest,
)
from backend.app.content.extractor import QuestionExtractorAgent
from backend.app.audit.service import record_audit_event


async def create_and_distribute_material(
    db: AsyncSession,
    actor: User,
    data: MaterialCreate,
) -> Material:
    """
    Creates a learning material and distributes it to specified sections.
    Enforces that teachers can ONLY share materials to sections they are assigned to teach.
    """
    # 1. Verify existence of class and subject
    cls = await db.get(Class, data.class_id)
    if not cls or cls.school_id != actor.school_id:
        raise NotFoundException("Class", data.class_id)

    subj = await db.get(Subject, data.subject_id)
    if not subj or subj.school_id != actor.school_id:
        raise NotFoundException("Subject", data.subject_id)

    # 2. Scope validation for teacher
    actor_roles = [r.role for r in getattr(actor, "_cached_role_assignments", []) if getattr(r, "status", None) == "active"]
    if not actor_roles and hasattr(actor, "primary_role"):
        actor_roles = [actor.primary_role]

    is_admin = RoleName.PLATFORM_ADMIN in actor_roles or RoleName.SCHOOL_ADMIN in actor_roles
    is_coordinator = RoleName.ACADEMIC_COORDINATOR in actor_roles

    if not is_admin and not is_coordinator:
        # Teacher must be assigned to teach this class and subject
        stmt = select(TeacherAssignment).where(
            TeacherAssignment.school_id == actor.school_id,
            TeacherAssignment.teacher_id == actor.id,
            TeacherAssignment.class_id == data.class_id,
            TeacherAssignment.subject_id == data.subject_id,
            TeacherAssignment.status == "active",
        )
        res = await db.execute(stmt)
        teacher_assignments = list(res.scalars().all())
        if not teacher_assignments:
            raise ForbiddenException("Teacher is not assigned to teach this subject and class.")

        assigned_section_ids = {a.section_id for a in teacher_assignments}
        # Check that EVERY requested target section is taught by this teacher
        for sec_id in data.target_section_ids:
            if sec_id not in assigned_section_ids:
                raise ForbiddenException(
                    f"Access denied: Teacher is not assigned to teach section {sec_id}."
                )

    # 3. Create Material record
    material = Material(
        school_id=actor.school_id,
        uploader_id=actor.id,
        subject_id=data.subject_id,
        class_id=data.class_id,
        title=data.title,
        description=data.description,
        file_url=data.file_url,
        file_type=data.file_type,
        file_size_bytes=data.file_size_bytes,
        chapter=data.chapter,
        topic=data.topic,
        content_text=data.content_text,
        status="active",
        expires_at=data.expires_at,
    )
    db.add(material)
    await db.flush()

    # 4. Create MaterialDistributions for specified sections
    if data.target_section_ids:
        # Validate sections exist in the class
        sec_stmt = select(Section).where(
            Section.id.in_(data.target_section_ids),
            Section.class_id == data.class_id,
        )
        sec_res = await db.execute(sec_stmt)
        valid_sections = list(sec_res.scalars().all())
        if len(valid_sections) != len(data.target_section_ids):
            raise ValidationException("One or more target sections do not belong to the selected class.")

        for sec in valid_sections:
            dist = MaterialDistribution(
                school_id=actor.school_id,
                material_id=material.id,
                section_id=sec.id,
                distributed_by=actor.id,
            )
            db.add(dist)

    await db.commit()
    await db.refresh(material)

    # Audit logging
    await record_audit_event(
        db=db,
        school_id=actor.school_id,
        action="material.upload",
        entity_type="material",
        entity_id=material.id,
        actor_id=actor.id,
        metadata_json={
            "title": material.title,
            "class_id": material.class_id,
            "subject_id": material.subject_id,
            "distributed_sections": data.target_section_ids,
        },
    )

    return material


async def list_materials_for_actor(
    db: AsyncSession,
    actor: User,
    class_id: Optional[str] = None,
    subject_id: Optional[str] = None,
) -> List[MaterialOut]:
    """
    Lists materials visible to a staff member (Teacher, Coordinator, Admin).
    """
    stmt = (
        select(Material)
        .options(
            selectinload(Material.distributions),
            selectinload(Material.engagements),
        )
        .where(
            Material.school_id == actor.school_id,
            Material.status == "active",
        )
        .order_by(desc(Material.created_at))
    )

    if class_id:
        stmt = stmt.where(Material.class_id == class_id)
    if subject_id:
        stmt = stmt.where(Material.subject_id == subject_id)

    res = await db.execute(stmt)
    materials = list(res.scalars().all())

    # Build response objects enriched with class and subject names
    class_ids = {m.class_id for m in materials}
    subject_ids = {m.subject_id for m in materials}

    classes_map = {}
    if class_ids:
        c_res = await db.execute(select(Class).where(Class.id.in_(class_ids)))
        classes_map = {c.id: c.name for c in c_res.scalars().all()}

    subjects_map = {}
    if subject_ids:
        s_res = await db.execute(select(Subject).where(Subject.id.in_(subject_ids)))
        subjects_map = {s.id: s.name for s in s_res.scalars().all()}

    section_ids = set()
    for m in materials:
        for d in m.distributions:
            section_ids.add(d.section_id)

    sections_map = {}
    if section_ids:
        sec_res = await db.execute(select(Section).where(Section.id.in_(section_ids)))
        sections_map = {sec.id: sec.name for sec in sec_res.scalars().all()}

    result = []
    for m in materials:
        dist_sec_ids = [d.section_id for d in m.distributions]
        dist_sec_names = [sections_map.get(s_id, s_id) for s_id in dist_sec_ids]
        unique_readers = len({e.student_id for e in m.engagements})

        result.append(
            MaterialOut(
                id=m.id,
                school_id=m.school_id,
                uploader_id=m.uploader_id,
                subject_id=m.subject_id,
                class_id=m.class_id,
                subject_name=subjects_map.get(m.subject_id, "Subject"),
                class_name=classes_map.get(m.class_id, "Class"),
                title=m.title,
                description=m.description,
                file_url=m.file_url,
                file_type=m.file_type,
                file_size_bytes=m.file_size_bytes,
                chapter=m.chapter,
                topic=m.topic,
                status=m.status,
                created_at=m.created_at,
                distributed_section_ids=dist_sec_ids,
                distributed_section_names=dist_sec_names,
                open_count=len(m.engagements),
                unique_readers_count=unique_readers,
            )
        )

    return result


async def get_material_detail(
    db: AsyncSession,
    actor: User,
    material_id: str,
) -> MaterialOut:
    """Fetches single material details."""
    stmt = (
        select(Material)
        .options(
            selectinload(Material.distributions),
            selectinload(Material.engagements),
        )
        .where(
            Material.id == material_id,
            Material.school_id == actor.school_id,
        )
    )
    res = await db.execute(stmt)
    m = res.scalar_one_or_none()
    if not m:
        raise NotFoundException("Material", material_id)

    cls = await db.get(Class, m.class_id)
    subj = await db.get(Subject, m.subject_id)

    dist_sec_ids = [d.section_id for d in m.distributions]
    sections_map = {}
    if dist_sec_ids:
        sec_res = await db.execute(select(Section).where(Section.id.in_(dist_sec_ids)))
        sections_map = {sec.id: sec.name for sec in sec_res.scalars().all()}

    dist_sec_names = [sections_map.get(s_id, s_id) for s_id in dist_sec_ids]
    unique_readers = len({e.student_id for e in m.engagements})

    return MaterialOut(
        id=m.id,
        school_id=m.school_id,
        uploader_id=m.uploader_id,
        subject_id=m.subject_id,
        class_id=m.class_id,
        subject_name=cls.name if cls else "Class",
        class_name=subj.name if subj else "Subject",
        title=m.title,
        description=m.description,
        file_url=m.file_url,
        file_type=m.file_type,
        file_size_bytes=m.file_size_bytes,
        chapter=m.chapter,
        topic=m.topic,
        status=m.status,
        created_at=m.created_at,
        distributed_section_ids=dist_sec_ids,
        distributed_section_names=dist_sec_names,
        open_count=len(m.engagements),
        unique_readers_count=unique_readers,
    )


async def delete_material(
    db: AsyncSession,
    actor: User,
    material_id: str,
) -> None:
    """Soft-deletes / archives a material."""
    stmt = select(Material).where(Material.id == material_id, Material.school_id == actor.school_id)
    res = await db.execute(stmt)
    m = res.scalar_one_or_none()
    if not m:
        raise NotFoundException("Material", material_id)

    m.status = "archived"
    await db.commit()

    await record_audit_event(
        db=db,
        school_id=actor.school_id,
        action="material.archive",
        entity_type="material",
        entity_id=material_id,
        actor_id=actor.id,
        metadata_json={"before_status": "active", "after_status": "archived"},
    )


# --- Student My Learning ---

async def list_materials_for_student(
    db: AsyncSession,
    student: User,
) -> List[StudentMaterialOut]:
    """
    Returns materials distributed to the sections where the student is actively enrolled.
    Enforces strict section scoping: students NEVER see materials for other sections.
    """
    # 1. Find active enrollments
    enrollment_stmt = select(StudentEnrollment).where(
        StudentEnrollment.student_id == student.id,
        StudentEnrollment.school_id == student.school_id,
        StudentEnrollment.status == "active",
    )
    enr_res = await db.execute(enrollment_stmt)
    enrollments = list(enr_res.scalars().all())

    if not enrollments:
        return []

    enrolled_section_ids = [e.section_id for e in enrollments]

    # 2. Query materials distributed to these sections
    stmt = (
        select(Material, MaterialDistribution)
        .join(MaterialDistribution, Material.id == MaterialDistribution.material_id)
        .where(
            Material.school_id == student.school_id,
            Material.status == "active",
            MaterialDistribution.section_id.in_(enrolled_section_ids),
        )
        .order_by(desc(Material.created_at))
    )
    res = await db.execute(stmt)
    rows = res.all()

    # Deduplicate by material_id in case material was distributed to multiple student sections
    seen_ids = set()
    materials: List[Material] = []
    for m, _ in rows:
        if m.id not in seen_ids:
            seen_ids.add(m.id)
            materials.append(m)

    if not materials:
        return []

    # 3. Fetch student's engagements to know if they opened it
    material_ids = [m.id for m in materials]
    eng_stmt = select(MaterialEngagement).where(
        MaterialEngagement.student_id == student.id,
        MaterialEngagement.material_id.in_(material_ids),
    )
    eng_res = await db.execute(eng_stmt)
    engagements = list(eng_res.scalars().all())
    eng_map = {e.material_id: e for e in engagements}

    # Fetch Class and Subject names
    class_ids = {m.class_id for m in materials}
    subject_ids = {m.subject_id for m in materials}

    classes_map = {}
    if class_ids:
        c_res = await db.execute(select(Class).where(Class.id.in_(class_ids)))
        classes_map = {c.id: c.name for c in c_res.scalars().all()}

    subjects_map = {}
    if subject_ids:
        s_res = await db.execute(select(Subject).where(Subject.id.in_(subject_ids)))
        subjects_map = {s.id: s.name for s in s_res.scalars().all()}

    student_materials = []
    for m in materials:
        eng = eng_map.get(m.id)
        student_materials.append(
            StudentMaterialOut(
                id=m.id,
                title=m.title,
                description=m.description,
                file_url=m.file_url,
                file_type=m.file_type,
                file_size_bytes=m.file_size_bytes,
                subject_id=m.subject_id,
                subject_name=subjects_map.get(m.subject_id, "Subject"),
                class_id=m.class_id,
                class_name=classes_map.get(m.class_id, "Class"),
                chapter=m.chapter,
                topic=m.topic,
                content_text=m.content_text,
                created_at=m.created_at,
                has_opened=bool(eng is not None),
                last_opened_at=eng.opened_at if eng else None,
            )
        )

    return student_materials


async def record_student_open_event(
    db: AsyncSession,
    student: User,
    material_id: str,
    duration_seconds: int = 0,
    pages_read: int = 1,
) -> MaterialEngagement:
    """
    Logs an open/engagement event when a student accesses a material.
    Verifies that the material is distributed to the student's enrolled section.
    """
    # 1. Fetch material
    mat = await db.get(Material, material_id)
    if not mat or mat.school_id != student.school_id or mat.status != "active":
        raise NotFoundException("Material", material_id)

    # 2. Verify student enrollment in target section
    dist_stmt = select(MaterialDistribution).where(
        MaterialDistribution.material_id == material_id
    )
    dist_res = await db.execute(dist_stmt)
    distributions = list(dist_res.scalars().all())
    distributed_section_ids = {d.section_id for d in distributions}

    enr_stmt = select(StudentEnrollment).where(
        StudentEnrollment.student_id == student.id,
        StudentEnrollment.school_id == student.school_id,
        StudentEnrollment.status == "active",
        StudentEnrollment.section_id.in_(distributed_section_ids),
    )
    enr_res = await db.execute(enr_stmt)
    matching_enrollment = enr_res.scalar_one_or_none()

    if not matching_enrollment:
        raise ForbiddenException("Student is not enrolled in any section with access to this material.")

    # 3. Create or update engagement record
    engagement = MaterialEngagement(
        school_id=student.school_id,
        material_id=material_id,
        student_id=student.id,
        section_id=matching_enrollment.section_id,
        opened_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
        pages_read=pages_read,
    )
    db.add(engagement)
    await db.commit()
    await db.refresh(engagement)

    await record_audit_event(
        db=db,
        school_id=student.school_id,
        action="material.open",
        entity_type="material",
        entity_id=material_id,
        actor_id=student.id,
        metadata_json={
            "duration_seconds": duration_seconds,
            "pages_read": pages_read,
            "section_id": matching_enrollment.section_id,
        },
    )

    return engagement


# --- Question Extractor Agent Integration ---

async def trigger_question_extraction(
    db: AsyncSession,
    actor: User,
    material_id: str,
    max_questions: int = 5,
) -> QuestionExtractionJob:
    """
    Extracts draft candidate questions from uploaded material text using QuestionExtractorAgent.
    Mandatory: Questions are saved in status='needs_review'.
    """
    mat = await db.get(Material, material_id)
    if not mat or mat.school_id != actor.school_id:
        raise NotFoundException("Material", material_id)

    subj = await db.get(Subject, mat.subject_id)
    subject_name = subj.name if subj else "General"

    raw_text = mat.content_text or f"{mat.title}\n{mat.description or ''}"
    if len(raw_text.strip()) < 20:
        raw_text = f"Chapter: {mat.chapter or mat.title}. Subject: {subject_name}. Core concepts and academic principles of {mat.title}."

    extractor = QuestionExtractorAgent()
    candidates = await extractor.extract_from_text(
        text=raw_text,
        subject_name=subject_name,
        chapter=mat.chapter,
        max_questions=max_questions,
    )

    job = QuestionExtractionJob(
        school_id=actor.school_id,
        material_id=material_id,
        requester_id=actor.id,
        status="succeeded",
        extracted_count=len(candidates),
        results_json=[c.model_dump() for c in candidates],
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    await record_audit_event(
        db=db,
        school_id=actor.school_id,
        action="question.extract",
        entity_type="material",
        entity_id=material_id,
        actor_id=actor.id,
        metadata_json={"job_id": job.id, "extracted_count": len(candidates)},
    )

    return job


async def approve_extracted_question(
    db: AsyncSession,
    actor: User,
    material_id: str,
    payload: QuestionApprovalRequest,
) -> Question:
    """
    Teacher explicitly accepts and approves a candidate extracted question into the Question Bank.
    Converts candidate from 'needs_review' into an active canonical Question.
    """
    mat = await db.get(Material, material_id)
    if not mat or mat.school_id != actor.school_id:
        raise NotFoundException("Material", material_id)

    q = Question(
        school_id=actor.school_id,
        author_id=actor.id,
        subject_id=mat.subject_id,
        category=payload.category or "written",
        type=payload.type or "short_answer",
        prompt=payload.prompt or "Extracted Question Prompt",
        marks=payload.marks or 1,
        difficulty=payload.difficulty or "medium",
        topic_tags=[mat.chapter] if mat.chapter else [],
        content_data={"options": payload.options} if payload.options else {},
        answer_data={
            "expected_answer": payload.expected_answer or "",
            "answer_keys": payload.answer_keys or [],
            "marking_scheme": payload.marking_scheme or "",
        },
        status="active",  # Approved by human teacher!
        version=1,
    )
    db.add(q)
    await db.commit()
    await db.refresh(q)

    await record_audit_event(
        db=db,
        school_id=actor.school_id,
        action="question.approve",
        entity_type="question",
        entity_id=q.id,
        actor_id=actor.id,
        metadata_json={"candidate_id": payload.candidate_question_id, "status": "active"},
    )

    return q
