"""
Roster & Student Credential Service — Mind V2
Handles:
1. Class Teacher section student additions with roll number uniqueness
2. Roster state machine: Pending -> Verified -> Locked
3. Post-lock RosterChangeRequest workflow (Class Teacher requests, Coordinator approves)
4. Student credential slip generation with forced first-login password change
"""
import csv
import io
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import (
    NotFoundException,
    ForbiddenException,
    ConflictException,
    ValidationException,
)
from backend.app.core.security import hash_password
from backend.app.audit.service import record_audit_event
from backend.app.tenancy.models import School, Band
from backend.app.identity.models import User, RoleAssignment, RoleName
from backend.app.academics.models import (
    Class,
    Section,
    TeacherAssignment,
    StudentEnrollment,
    RosterChangeRequest,
)
from backend.app.academics.schemas import (
    StudentCreateRequest,
    StudentCredentialSlipResponse,
    StudentEnrollmentResponse,
    SectionRosterResponse,
    RosterChangeCreateRequest,
    RosterChangeReviewRequest,
    RosterChangeResponse,
)


async def verify_class_teacher_authority(
    db: AsyncSession,
    actor: User,
    section: Section,
) -> bool:
    """
    Verifies if the actor has Class Teacher or supervisory authority over the section.
    Authorized actors:
    - Platform Admin
    - School Admin of this school
    - Academic Coordinator of this band
    - Designated Class Teacher of this specific section (is_class_teacher == True)
    """
    roles = {r.role for r in actor.role_assignments if r.status == "active"}

    if RoleName.PLATFORM_ADMIN in roles:
        return True

    if RoleName.SCHOOL_ADMIN in roles and actor.school_id == section.class_obj.school_id:
        return True

    if RoleName.ACADEMIC_COORDINATOR in roles:
        # Check if section's class belongs to coordinator's band
        asgn = next((r for r in actor.role_assignments if r.role == RoleName.ACADEMIC_COORDINATOR and r.status == "active"), None)
        if asgn and asgn.band_id:
            cls = section.class_obj
            if cls.band_id == asgn.band_id:
                return True
            if cls.grade_level:
                band = await db.get(Band, asgn.band_id)
                if band and band.min_grade <= cls.grade_level <= band.max_grade:
                    return True

    # Check if teacher is designated Class Teacher for this section
    ct_stmt = select(TeacherAssignment).where(
        TeacherAssignment.school_id == actor.school_id,
        TeacherAssignment.teacher_id == actor.id,
        TeacherAssignment.section_id == section.id,
        TeacherAssignment.is_class_teacher == True,
        TeacherAssignment.status == "active",
    )
    ct_res = await db.execute(ct_stmt)
    if ct_res.scalars().first():
        return True

    return False


async def get_section_with_class(db: AsyncSession, section_id: str) -> Section:
    stmt = (
        select(Section)
        .options(selectinload(Section.class_obj))
        .where(Section.id == section_id)
    )
    res = await db.execute(stmt)
    section = res.scalar_one_or_none()
    if not section:
        raise NotFoundException("Section", section_id)
    return section


async def get_section_roster(
    db: AsyncSession,
    actor: User,
    section_id: str,
) -> SectionRosterResponse:
    """Fetches the section roster, enrolled students, designated Class Teacher, and status."""
    section = await get_section_with_class(db, section_id)

    # Fetch students
    enr_stmt = (
        select(StudentEnrollment)
        .options(selectinload(StudentEnrollment.student))
        .where(
            StudentEnrollment.school_id == section.class_obj.school_id,
            StudentEnrollment.section_id == section_id,
            StudentEnrollment.status == "active",
        )
        .order_by(StudentEnrollment.roll_number.asc())
    )
    enr_res = await db.execute(enr_stmt)
    enrollments = enr_res.scalars().all()

    # Fetch designated class teacher
    ct_stmt = (
        select(TeacherAssignment)
        .options(selectinload(TeacherAssignment.teacher))
        .where(
            TeacherAssignment.school_id == section.class_obj.school_id,
            TeacherAssignment.section_id == section_id,
            TeacherAssignment.is_class_teacher == True,
            TeacherAssignment.status == "active",
        )
    )
    ct_res = await db.execute(ct_stmt)
    ct_asgn = ct_res.scalars().first()

    students_resp = []
    for e in enrollments:
        students_resp.append(
            StudentEnrollmentResponse(
                id=e.id,
                school_id=e.school_id,
                student_id=e.student_id,
                class_id=e.class_id,
                section_id=e.section_id,
                roll_number=e.roll_number,
                status=e.status,
                student_name=e.student.full_name if e.student else None,
                class_name=section.class_obj.name,
                section_name=section.name,
                created_at=e.created_at,
            )
        )

    return SectionRosterResponse(
        section_id=section.id,
        section_name=section.name,
        class_id=section.class_obj.id,
        class_name=section.class_obj.name,
        roster_status=section.roster_status,
        class_teacher_id=ct_asgn.teacher_id if ct_asgn else None,
        class_teacher_name=ct_asgn.teacher.full_name if ct_asgn and ct_asgn.teacher else None,
        students=students_resp,
        total_students=len(students_resp),
    )


async def add_student_to_section(
    db: AsyncSession,
    actor: User,
    section_id: str,
    data: StudentCreateRequest,
) -> StudentCredentialSlipResponse:
    """Class Teacher or Coordinator adds a student to the section roster."""
    section = await get_section_with_class(db, section_id)
    school = await db.get(School, section.class_obj.school_id)
    if not school:
        raise NotFoundException("School", section.class_obj.school_id)

    # 1. Check authority
    is_authorized = await verify_class_teacher_authority(db, actor, section)
    if not is_authorized:
        raise ForbiddenException(
            "Access Denied: Only the designated Class Teacher of this section or Academic Coordinator can modify this roster."
        )

    # 2. Check roster lock state
    if section.roster_status == "locked":
        raise ConflictException(
            "This roster is currently locked. New students or roll modifications require an approved Roster Change Request."
        )

    roll_clean = data.roll_number.strip()

    # 3. Check roll number uniqueness within this section and academic year
    dup_stmt = select(StudentEnrollment).where(
        StudentEnrollment.school_id == school.id,
        StudentEnrollment.section_id == section.id,
        StudentEnrollment.roll_number == roll_clean,
        StudentEnrollment.status == "active",
    )
    if section.class_obj.academic_year_id:
        dup_stmt = dup_stmt.where(
            (StudentEnrollment.academic_year_id == section.class_obj.academic_year_id) |
            (StudentEnrollment.academic_year_id.is_(None))
        )
    dup_res = await db.execute(dup_stmt)
    if dup_res.scalars().first():
        raise ConflictException(
            f"Roll number '{roll_clean}' is already assigned in Section {section.name}."
        )

    # 4. Generate login email and temporary password
    initial_password = data.password or f"Mind@{roll_clean}"
    if data.email:
        login_email = data.email.lower().strip()
    else:
        # Standardized student login ID: s.<school_code>.<class>.<section>.<roll>@mind.local
        code = school.code or school.slug
        clean_class = section.class_obj.name.replace(" ", "").lower()
        login_email = f"s.{code.lower()}.{clean_class}.{section.name.lower()}.{roll_clean.lower()}@mind.local"

    # Check if user already exists
    u_stmt = select(User).where(User.school_id == school.id, User.email == login_email)
    u_res = await db.execute(u_stmt)
    student = u_res.scalar_one_or_none()

    if not student:
        student = User(
            school_id=school.id,
            email=login_email,
            password_hash=hash_password(initial_password),
            full_name=data.full_name.strip(),
            status="active",
            must_change_password=True,
        )
        db.add(student)
        await db.flush()

        # Student role assignment
        ra = RoleAssignment(
            user_id=student.id,
            role=RoleName.STUDENT,
            school_id=school.id,
            status="active",
        )
        db.add(ra)
        await db.flush()

    # 5. Create student enrollment
    enrollment = StudentEnrollment(
        school_id=school.id,
        student_id=student.id,
        academic_year_id=section.class_obj.academic_year_id,
        class_id=section.class_obj.id,
        section_id=section.id,
        roll_number=roll_clean,
        status="active",
    )
    db.add(enrollment)
    await db.flush()

    # 6. Audit event
    await record_audit_event(
        db=db,
        school_id=school.id,
        actor_id=actor.id,
        action="roster.student_added",
        entity_type="student_enrollment",
        entity_id=enrollment.id,
        metadata_json={
            "student_id": student.id,
            "roll_number": roll_clean,
            "section_id": section.id,
            "class_id": section.class_obj.id,
        },
    )

    return StudentCredentialSlipResponse(
        student_id=student.id,
        full_name=student.full_name,
        roll_number=roll_clean,
        login_email=student.email,
        initial_password=initial_password,
        class_name=section.class_obj.name,
        section_name=section.name,
        school_name=school.name,
        must_change_password=student.must_change_password,
    )


async def bulk_add_students_csv(
    db: AsyncSession,
    actor: User,
    section_id: str,
    csv_content: str,
) -> Dict[str, Any]:
    """Bulk imports students from CSV into a section roster."""
    section = await get_section_with_class(db, section_id)
    is_authorized = await verify_class_teacher_authority(db, actor, section)
    if not is_authorized:
        raise ForbiddenException("Only the designated Class Teacher or Academic Coordinator can import students.")

    if section.roster_status == "locked":
        raise ConflictException("Roster is locked. Modifications require an approved Roster Change Request.")

    reader = csv.DictReader(io.StringIO(csv_content))
    imported = []
    errors = []

    for idx, row in enumerate(reader, start=1):
        full_name = row.get("full_name") or row.get("name")
        roll = row.get("roll_number") or row.get("roll")
        email = row.get("email")

        if not full_name or not roll:
            errors.append({"row": idx, "error": "Missing required 'full_name' or 'roll_number'"})
            continue

        try:
            req = StudentCreateRequest(
                full_name=full_name.strip(),
                roll_number=roll.strip(),
                email=email.strip() if email else None,
            )
            slip = await add_student_to_section(db, actor, section_id, req)
            imported.append(slip)
        except Exception as ex:
            errors.append({"row": idx, "roll_number": roll, "error": str(ex)})

    return {
        "total_rows": idx if "idx" in locals() else 0,
        "imported_count": len(imported),
        "error_count": len(errors),
        "slips": imported,
        "errors": errors,
    }


async def update_roster_status(
    db: AsyncSession,
    actor: User,
    section_id: str,
    new_status: str,
) -> Dict[str, Any]:
    """Transitions section roster status: pending -> verified -> locked."""
    section = await get_section_with_class(db, section_id)
    is_authorized = await verify_class_teacher_authority(db, actor, section)
    if not is_authorized:
        raise ForbiddenException("Only the designated Class Teacher or Academic Coordinator can change roster status.")

    old_status = section.roster_status
    section.roster_status = new_status
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=section.class_obj.school_id,
        actor_id=actor.id,
        action="roster.status_updated",
        entity_type="section",
        entity_id=section.id,
        metadata_json={"old_status": old_status, "new_status": new_status},
    )

    return {"section_id": section.id, "roster_status": section.roster_status}


async def request_roster_change(
    db: AsyncSession,
    actor: User,
    section_id: str,
    data: RosterChangeCreateRequest,
) -> RosterChangeResponse:
    """Class Teacher submits a change request for a locked section roster."""
    section = await get_section_with_class(db, section_id)

    req = RosterChangeRequest(
        school_id=section.class_obj.school_id,
        section_id=section.id,
        requested_by_id=actor.id,
        change_type=data.change_type,
        student_data=data.student_data,
        reason=data.reason,
        status="pending",
    )
    db.add(req)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=section.class_obj.school_id,
        actor_id=actor.id,
        action="roster_change.requested",
        entity_type="roster_change_request",
        entity_id=req.id,
        metadata_json={"section_id": section.id, "change_type": data.change_type},
    )

    return RosterChangeResponse(
        id=req.id,
        section_id=req.section_id,
        requested_by_id=req.requested_by_id,
        requested_by_name=actor.full_name,
        change_type=req.change_type,
        student_data=req.student_data,
        reason=req.reason,
        status=req.status,
        created_at=req.created_at,
    )


async def review_roster_change(
    db: AsyncSession,
    actor: User,
    request_id: str,
    review: RosterChangeReviewRequest,
) -> RosterChangeResponse:
    """Academic Coordinator or School Admin reviews and executes a roster change request."""
    req = await db.get(RosterChangeRequest, request_id)
    if not req:
        raise NotFoundException("RosterChangeRequest", request_id)

    section = await get_section_with_class(db, req.section_id)

    # Check supervisory authority (Coordinator of band or Admin)
    roles = {r.role for r in actor.role_assignments if r.status == "active"}
    has_coord_power = RoleName.SCHOOL_ADMIN in roles or RoleName.PLATFORM_ADMIN in roles
    if not has_coord_power and RoleName.ACADEMIC_COORDINATOR in roles:
        asgn = next((r for r in actor.role_assignments if r.role == RoleName.ACADEMIC_COORDINATOR and r.status == "active"), None)
        if asgn and asgn.band_id:
            cls = section.class_obj
            if cls.band_id == asgn.band_id:
                has_coord_power = True
            elif cls.grade_level:
                band = await db.get(Band, asgn.band_id)
                if band and band.min_grade <= cls.grade_level <= band.max_grade:
                    has_coord_power = True

    if not has_coord_power:
        raise ForbiddenException("Only the Academic Coordinator or School Admin can review roster change requests.")

    req.status = review.status
    req.reviewed_by_id = actor.id
    req.reviewed_at = datetime.now(timezone.utc)
    req.review_notes = review.review_notes

    # If approved and change_type is add_student, execute the addition
    if review.status == "approved" and req.change_type == "add_student":
        student_info = req.student_data
        create_req = StudentCreateRequest(
            full_name=student_info.get("full_name", "Student"),
            roll_number=student_info.get("roll_number", "0"),
            email=student_info.get("email"),
        )
        # Temporarily unlock or execute addition
        orig_status = section.roster_status
        section.roster_status = "verified"  # Temporarily allow addition
        await add_student_to_section(db, actor, section.id, create_req)
        section.roster_status = orig_status

    await db.flush()

    await record_audit_event(
        db=db,
        school_id=section.class_obj.school_id,
        actor_id=actor.id,
        action=f"roster_change.{review.status}",
        entity_type="roster_change_request",
        entity_id=req.id,
        metadata_json={"reviewer_id": actor.id, "status": review.status},
    )

    req_user = await db.get(User, req.requested_by_id)

    return RosterChangeResponse(
        id=req.id,
        section_id=req.section_id,
        requested_by_id=req.requested_by_id,
        requested_by_name=req_user.full_name if req_user else None,
        change_type=req.change_type,
        student_data=req.student_data,
        reason=req.reason,
        status=req.status,
        reviewed_by_id=req.reviewed_by_id,
        reviewed_at=req.reviewed_at,
        review_notes=req.review_notes,
        created_at=req.created_at,
    )


async def list_roster_changes(
    db: AsyncSession,
    actor: User,
    section_id: Optional[str] = None,
) -> List[RosterChangeResponse]:
    stmt = (
        select(RosterChangeRequest)
        .options(selectinload(RosterChangeRequest.requested_by))
        .where(RosterChangeRequest.school_id == actor.school_id)
        .order_by(RosterChangeRequest.created_at.desc())
    )
    if section_id:
        stmt = stmt.where(RosterChangeRequest.section_id == section_id)

    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        RosterChangeResponse(
            id=r.id,
            section_id=r.section_id,
            requested_by_id=r.requested_by_id,
            requested_by_name=r.requested_by.full_name if r.requested_by else None,
            change_type=r.change_type,
            student_data=r.student_data,
            reason=r.reason,
            status=r.status,
            reviewed_by_id=r.reviewed_by_id,
            reviewed_at=r.reviewed_at,
            review_notes=r.review_notes,
            created_at=r.created_at,
        )
        for r in records
    ]


async def get_credential_slips(
    db: AsyncSession,
    actor: User,
    section_id: str,
) -> List[StudentCredentialSlipResponse]:
    """Generates credential distribution slips for all enrolled students in the section."""
    section = await get_section_with_class(db, section_id)
    school = await db.get(School, section.class_obj.school_id)

    enr_stmt = (
        select(StudentEnrollment)
        .options(selectinload(StudentEnrollment.student))
        .where(
            StudentEnrollment.school_id == school.id,
            StudentEnrollment.section_id == section_id,
            StudentEnrollment.status == "active",
        )
        .order_by(StudentEnrollment.roll_number.asc())
    )
    enr_res = await db.execute(enr_stmt)
    enrollments = enr_res.scalars().all()

    slips = []
    for e in enrollments:
        if e.student:
            slips.append(
                StudentCredentialSlipResponse(
                    student_id=e.student.id,
                    full_name=e.student.full_name,
                    roll_number=e.roll_number or "N/A",
                    login_email=e.student.email,
                    initial_password=f"Mind@{e.roll_number}",
                    class_name=section.class_obj.name,
                    section_name=section.name,
                    school_name=school.name if school else "Mind Academy",
                    must_change_password=e.student.must_change_password,
                )
            )
    return slips
