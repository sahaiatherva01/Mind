"""
Coordinator Service — Mind V2
Handles Academic Coordinator operations strictly scoped to the assigned grade band.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    ConflictException,
)
from backend.app.core.security import hash_password
from backend.app.audit.service import record_audit_event
from backend.app.tenancy.models import Band
from backend.app.identity.models import User, RoleAssignment, RoleName
from backend.app.academics.models import (
    Class,
    Section,
    Subject,
    TeacherAssignment,
    StudentEnrollment,
    CurriculumNode,
)
from backend.app.academics.schemas import (
    ClassResponse,
    SectionResponse,
    BandSummaryResponse,
    AssignmentMatrixItem,
    CoordinatorTeacherCreateRequest,
    TeacherAssignmentCreateRequest,
    CurriculumNodeResponse,
)
from backend.app.academics.service import create_teacher_assignment


async def get_coordinator_band(db: AsyncSession, coordinator: User) -> Band:
    """Retrieves the active Band entity for the given coordinator."""
    # Find active coordinator assignment
    stmt = select(RoleAssignment).where(
        RoleAssignment.user_id == coordinator.id,
        RoleAssignment.role == RoleName.ACADEMIC_COORDINATOR,
        RoleAssignment.status == "active",
    )
    res = await db.execute(stmt)
    asgn = res.scalars().first()
    if not asgn or not asgn.band_id:
        raise ForbiddenException("User is not assigned as an active Academic Coordinator to any grade band.")

    band = await db.get(Band, asgn.band_id)
    if not band:
        raise NotFoundException("Band", asgn.band_id)
    return band


async def get_band_classes(db: AsyncSession, band: Band) -> List[Class]:
    """Retrieves all classes belonging to the given band (by band_id or grade_level)."""
    stmt = (
        select(Class)
        .options(selectinload(Class.sections))
        .where(
            Class.school_id == band.school_id,
            (Class.band_id == band.id) |
            (and_(Class.grade_level >= band.min_grade, Class.grade_level <= band.max_grade))
        )
    )
    res = await db.execute(stmt)
    return res.scalars().all()


async def get_band_summary(db: AsyncSession, coordinator: User) -> BandSummaryResponse:
    """Aggregates metrics and class structure for the coordinator's band."""
    band = await get_coordinator_band(db, coordinator)
    classes = await get_band_classes(db, band)
    class_ids = [c.id for c in classes]

    sections_count = sum(len(c.sections) for c in classes)

    # Distinct teachers in this band
    if class_ids:
        t_stmt = select(func.count(func.distinct(TeacherAssignment.teacher_id))).where(
            TeacherAssignment.school_id == band.school_id,
            TeacherAssignment.class_id.in_(class_ids),
            TeacherAssignment.status == "active",
        )
        t_res = await db.execute(t_stmt)
        total_teachers = t_res.scalar() or 0

        # Distinct enrolled students in this band
        s_stmt = select(func.count(func.distinct(StudentEnrollment.student_id))).where(
            StudentEnrollment.school_id == band.school_id,
            StudentEnrollment.class_id.in_(class_ids),
            StudentEnrollment.status == "active",
        )
        s_res = await db.execute(s_stmt)
        total_students = s_res.scalar() or 0

        # Class teacher map
        ct_stmt = (
            select(TeacherAssignment)
            .options(selectinload(TeacherAssignment.teacher))
            .where(
                TeacherAssignment.school_id == band.school_id,
                TeacherAssignment.class_id.in_(class_ids),
                TeacherAssignment.is_class_teacher == True,
                TeacherAssignment.status == "active",
            )
        )
        ct_res = await db.execute(ct_stmt)
        class_teachers_map = {
            asgn.section_id: (asgn.teacher.full_name if asgn.teacher else None)
            for asgn in ct_res.scalars().all()
        }
    else:
        total_teachers = 0
        total_students = 0
        class_teachers_map = {}

    return BandSummaryResponse(
        band_id=band.id,
        band_name=band.name,
        min_grade=band.min_grade,
        max_grade=band.max_grade,
        classes=[ClassResponse.model_validate(c) for c in classes],
        total_classes=len(classes),
        total_sections=sections_count,
        total_teachers=total_teachers,
        total_students=total_students,
        class_teachers=class_teachers_map,
    )


async def list_band_teachers(db: AsyncSession, coordinator: User) -> List[Dict[str, Any]]:
    """Lists distinct teachers who have active assignments within the coordinator's band."""
    band = await get_coordinator_band(db, coordinator)
    classes = await get_band_classes(db, band)
    class_ids = [c.id for c in classes]

    if not class_ids:
        return []

    stmt = (
        select(User)
        .join(TeacherAssignment, TeacherAssignment.teacher_id == User.id)
        .options(selectinload(User.role_assignments))
        .where(
            TeacherAssignment.school_id == band.school_id,
            TeacherAssignment.class_id.in_(class_ids),
        )
        .distinct()
    )
    res = await db.execute(stmt)
    teachers = res.scalars().all()

    result = []
    for t in teachers:
        result.append({
            "id": t.id,
            "school_id": t.school_id,
            "email": t.email,
            "full_name": t.full_name,
            "designation": t.designation,
            "status": t.status,
            "primary_role": t.primary_role,
        })
    return result


async def create_band_teacher(
    db: AsyncSession,
    coordinator: User,
    data: CoordinatorTeacherCreateRequest,
) -> Dict[str, Any]:
    """Provisions a new teacher account and assigns them to a class in the coordinator's band."""
    band = await get_coordinator_band(db, coordinator)
    classes = await get_band_classes(db, band)
    valid_class_ids = {c.id for c in classes}

    if data.class_id not in valid_class_ids:
        raise ForbiddenException("Access Denied: The target class does not belong to your assigned grade band.")

    email_clean = data.email.lower().strip()
    # Check if user already exists
    u_stmt = select(User).where(User.school_id == band.school_id, User.email == email_clean)
    u_res = await db.execute(u_stmt)
    teacher = u_res.scalar_one_or_none()

    if not teacher:
        teacher = User(
            school_id=band.school_id,
            email=email_clean,
            password_hash=hash_password(data.password or "TeacherPass123!"),
            full_name=data.full_name.strip(),
            designation=data.designation or "Faculty Member",
            status="active",
            must_change_password=True,
        )
        db.add(teacher)
        await db.flush()

        # Add teacher role assignment
        ra = RoleAssignment(
            user_id=teacher.id,
            role=RoleName.TEACHER,
            school_id=band.school_id,
            status="active",
        )
        db.add(ra)
        await db.flush()

        await record_audit_event(
            db=db,
            school_id=band.school_id,
            actor_id=coordinator.id,
            action="coordinator.teacher_created",
            entity_type="user",
            entity_id=teacher.id,
            metadata_json={"email": teacher.email, "band_id": band.id},
        )

    # Now create assignment
    assignment_req = TeacherAssignmentCreateRequest(
        teacher_id=teacher.id,
        class_id=data.class_id,
        section_id=data.section_id,
        subject_id=data.subject_id,
        is_class_teacher=data.is_class_teacher,
    )
    assignment = await create_teacher_assignment(
        db=db,
        school_id=band.school_id,
        data=assignment_req,
        actor_id=coordinator.id,
    )

    return {
        "teacher": {
            "id": teacher.id,
            "email": teacher.email,
            "full_name": teacher.full_name,
            "designation": teacher.designation,
            "status": teacher.status,
        },
        "assignment": assignment,
    }


async def toggle_band_teacher_status(
    db: AsyncSession,
    coordinator: User,
    teacher_id: str,
    active: bool,
) -> Dict[str, Any]:
    """Toggles active status of a teacher who teaches in this coordinator's band."""
    band = await get_coordinator_band(db, coordinator)
    classes = await get_band_classes(db, band)
    valid_class_ids = {c.id for c in classes}

    # Verify teacher is assigned in this band
    asgn_stmt = select(TeacherAssignment).where(
        TeacherAssignment.school_id == band.school_id,
        TeacherAssignment.teacher_id == teacher_id,
        TeacherAssignment.class_id.in_(valid_class_ids),
    )
    asgn_res = await db.execute(asgn_stmt)
    if not asgn_res.scalars().first():
        raise ForbiddenException("Access Denied: Teacher has no active assignments within your assigned grade band.")

    teacher = await db.get(User, teacher_id)
    if not teacher or teacher.school_id != band.school_id:
        raise NotFoundException("Teacher", teacher_id)

    new_status = "active" if active else "inactive"
    teacher.status = new_status
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=band.school_id,
        actor_id=coordinator.id,
        action="coordinator.teacher_status_toggled",
        entity_type="user",
        entity_id=teacher.id,
        metadata_json={"new_status": new_status, "band_id": band.id},
    )

    return {"id": teacher.id, "email": teacher.email, "status": teacher.status}


async def get_assignment_matrix(
    db: AsyncSession,
    coordinator: User,
) -> List[AssignmentMatrixItem]:
    """Fetches the complete Teacher x Class x Section x Subject assignment matrix for this band."""
    band = await get_coordinator_band(db, coordinator)
    classes = await get_band_classes(db, band)
    valid_class_ids = {c.id for c in classes}

    if not valid_class_ids:
        return []

    stmt = (
        select(TeacherAssignment)
        .options(
            selectinload(TeacherAssignment.teacher),
            selectinload(TeacherAssignment.class_obj),
            selectinload(TeacherAssignment.section),
            selectinload(TeacherAssignment.subject),
        )
        .where(
            TeacherAssignment.school_id == band.school_id,
            TeacherAssignment.class_id.in_(valid_class_ids),
        )
        .order_by(TeacherAssignment.created_at.desc())
    )
    res = await db.execute(stmt)
    assignments = res.scalars().all()

    matrix = []
    for a in assignments:
        matrix.append(
            AssignmentMatrixItem(
                id=a.id,
                teacher_id=a.teacher_id,
                teacher_name=a.teacher.full_name if a.teacher else "Unknown",
                teacher_email=a.teacher.email if a.teacher else "Unknown",
                class_id=a.class_id,
                class_name=a.class_obj.name if a.class_obj else "Unknown",
                section_id=a.section_id,
                section_name=a.section.name if a.section else "Unknown",
                subject_id=a.subject_id,
                subject_name=a.subject.name if a.subject else "Unknown",
                subject_code=a.subject.code if a.subject else "Unknown",
                is_class_teacher=a.is_class_teacher,
                status=a.status,
            )
        )
    return matrix


async def assign_teacher_in_band(
    db: AsyncSession,
    coordinator: User,
    data: TeacherAssignmentCreateRequest,
) -> Dict[str, Any]:
    """Creates a new teacher assignment strictly within the coordinator's band."""
    band = await get_coordinator_band(db, coordinator)
    classes = await get_band_classes(db, band)
    valid_class_ids = {c.id for c in classes}

    if data.class_id not in valid_class_ids:
        raise ForbiddenException("Access Denied: The target class does not belong to your assigned grade band.")

    return await create_teacher_assignment(
        db=db,
        school_id=band.school_id,
        data=data,
        actor_id=coordinator.id,
    )


async def delete_band_assignment(
    db: AsyncSession,
    coordinator: User,
    assignment_id: str,
) -> None:
    """Removes a teacher assignment strictly within the coordinator's band."""
    band = await get_coordinator_band(db, coordinator)
    classes = await get_band_classes(db, band)
    valid_class_ids = {c.id for c in classes}

    assignment = await db.get(TeacherAssignment, assignment_id)
    if not assignment or assignment.school_id != band.school_id:
        raise NotFoundException("TeacherAssignment", assignment_id)

    if assignment.class_id not in valid_class_ids:
        raise ForbiddenException("Access Denied: Assignment class does not belong to your assigned grade band.")

    await db.delete(assignment)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=band.school_id,
        actor_id=coordinator.id,
        action="coordinator.assignment_deleted",
        entity_type="teacher_assignment",
        entity_id=assignment_id,
        metadata_json={"band_id": band.id},
    )


async def list_band_curriculum(
    db: AsyncSession,
    coordinator: User,
) -> List[CurriculumNodeResponse]:
    """Fetches syllabus chapters and topics for grades matching the coordinator's band."""
    band = await get_coordinator_band(db, coordinator)
    grade_strings = [str(g) for g in range(band.min_grade, band.max_grade + 1)]

    stmt = (
        select(CurriculumNode)
        .where(
            CurriculumNode.school_id == band.school_id,
            CurriculumNode.grade.in_(grade_strings),
        )
        .order_by(CurriculumNode.subject_id, CurriculumNode.chapter, CurriculumNode.topic)
    )
    res = await db.execute(stmt)
    nodes = res.scalars().all()
    return [CurriculumNodeResponse.model_validate(n) for n in nodes]
