"""
Academics Business Logic Service
"""
import io
import csv
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import openpyxl

from backend.app.core.errors import (
    ConflictException,
    NotFoundException,
    ValidationException,
    ForbiddenException,
)
from backend.app.core.security import hash_password
from backend.app.identity.models import User, RoleAssignment, RoleName
from backend.app.tenancy.models import AcademicYear
from backend.app.academics.models import (
    Class,
    Section,
    Subject,
    TeacherAssignment,
    StudentEnrollment,
    CurriculumNode,
)
from backend.app.academics.schemas import (
    ClassCreateRequest,
    SectionCreateRequest,
    SubjectCreateRequest,
    TeacherAssignmentCreateRequest,
    StudentEnrollmentCreateRequest,
    CurriculumNodeCreateRequest,
    BulkImportResponse,
    BulkImportRowError,
)
from backend.app.audit.service import record_audit_event


# ------------------- CLASSES & SECTIONS -------------------

async def list_classes(db: AsyncSession, school_id: str, academic_year_id: Optional[str] = None) -> List[Class]:
    stmt = (
        select(Class)
        .options(selectinload(Class.sections))
        .where(Class.school_id == school_id)
    )
    if academic_year_id:
        stmt = stmt.where(Class.academic_year_id == academic_year_id)
    stmt = stmt.order_by(Class.name)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def create_class(
    db: AsyncSession,
    school_id: str,
    data: ClassCreateRequest,
    actor_id: Optional[str] = None
) -> Class:
    stmt = select(Class).where(
        Class.school_id == school_id,
        Class.academic_year_id == data.academic_year_id,
        Class.name == data.name.strip()
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException(f"Class '{data.name}' already exists in this academic year")

    new_class = Class(
        school_id=school_id,
        academic_year_id=data.academic_year_id,
        name=data.name.strip(),
    )
    db.add(new_class)
    await db.flush()

    # Create initial sections if requested (e.g., A, B, C)
    if data.section_names:
        for s_name in data.section_names:
            clean_s = s_name.strip()
            if clean_s:
                sec = Section(class_id=new_class.id, name=clean_s)
                db.add(sec)
        await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="class.created",
        entity_type="class",
        entity_id=new_class.id,
        metadata_json={"name": new_class.name},
    )

    # Reload with sections
    stmt = select(Class).options(selectinload(Class.sections)).where(Class.id == new_class.id)
    res = await db.execute(stmt)
    return res.scalar_one()


async def create_section(
    db: AsyncSession,
    class_id: str,
    data: SectionCreateRequest,
    school_id: str,
    actor_id: Optional[str] = None
) -> Section:
    stmt_class = select(Class).where(Class.id == class_id, Class.school_id == school_id)
    res_class = await db.execute(stmt_class)
    class_obj = res_class.scalar_one_or_none()
    if not class_obj:
        raise NotFoundException("Class", class_id)

    stmt = select(Section).where(Section.class_id == class_id, Section.name == data.name.strip())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException(f"Section '{data.name}' already exists in this class")

    section = Section(class_id=class_id, name=data.name.strip())
    db.add(section)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="section.created",
        entity_type="section",
        entity_id=section.id,
        metadata_json={"class_id": class_id, "name": section.name},
    )

    return section


# ------------------- SUBJECTS -------------------

async def list_subjects(db: AsyncSession, school_id: str) -> List[Subject]:
    stmt = select(Subject).where(Subject.school_id == school_id).order_by(Subject.name)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def create_subject(
    db: AsyncSession,
    school_id: str,
    data: SubjectCreateRequest,
    actor_id: Optional[str] = None
) -> Subject:
    code_clean = data.code.strip().upper()
    stmt = select(Subject).where(Subject.school_id == school_id, Subject.code == code_clean)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictException(f"Subject with code '{code_clean}' already exists")

    subject = Subject(
        school_id=school_id,
        name=data.name.strip(),
        code=code_clean,
    )
    db.add(subject)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="subject.created",
        entity_type="subject",
        entity_id=subject.id,
        metadata_json={"name": subject.name, "code": subject.code},
    )

    return subject


# ------------------- TEACHER ASSIGNMENTS -------------------

async def list_teacher_assignments(
    db: AsyncSession,
    school_id: str,
    teacher_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    stmt = (
        select(TeacherAssignment)
        .options(
            selectinload(TeacherAssignment.teacher),
            selectinload(TeacherAssignment.class_obj),
            selectinload(TeacherAssignment.section),
            selectinload(TeacherAssignment.subject),
        )
        .where(TeacherAssignment.school_id == school_id)
    )
    if teacher_id:
        stmt = stmt.where(TeacherAssignment.teacher_id == teacher_id)

    res = await db.execute(stmt)
    assignments = res.scalars().all()

    output = []
    for a in assignments:
        output.append({
            "id": a.id,
            "school_id": a.school_id,
            "teacher_id": a.teacher_id,
            "class_id": a.class_id,
            "section_id": a.section_id,
            "subject_id": a.subject_id,
            "teacher_name": a.teacher.full_name if a.teacher else None,
            "class_name": a.class_obj.name if a.class_obj else None,
            "section_name": a.section.name if a.section else None,
            "subject_name": a.subject.name if a.subject else None,
            "created_at": a.created_at,
        })
    return output


async def create_teacher_assignment(
    db: AsyncSession,
    school_id: str,
    data: TeacherAssignmentCreateRequest,
    actor_id: Optional[str] = None
) -> Dict[str, Any]:
    # Verify teacher exists and has teacher role
    user_stmt = select(User).where(User.id == data.teacher_id, User.school_id == school_id)
    u_res = await db.execute(user_stmt)
    teacher = u_res.scalar_one_or_none()
    teacher_roles = [r.role for r in teacher.role_assignments if r.status == "active"] if teacher else []
    if not teacher or not ({"teacher", "admin", "school_admin", "academic_coordinator"}.intersection(teacher_roles) or teacher.role in ("teacher", "admin", "school_admin")):
        raise ValidationException("Assigned user must exist and have role 'teacher' or 'admin'")


    # Check duplicate assignment
    dup_stmt = select(TeacherAssignment).where(
        TeacherAssignment.school_id == school_id,
        TeacherAssignment.teacher_id == data.teacher_id,
        TeacherAssignment.class_id == data.class_id,
        TeacherAssignment.section_id == data.section_id,
        TeacherAssignment.subject_id == data.subject_id,
    )
    res_dup = await db.execute(dup_stmt)
    if res_dup.scalar_one_or_none():
        raise ConflictException("This teacher is already assigned to this class, section, and subject")

    assignment = TeacherAssignment(
        school_id=school_id,
        teacher_id=data.teacher_id,
        class_id=data.class_id,
        section_id=data.section_id,
        subject_id=data.subject_id,
    )
    db.add(assignment)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="teacher_assignment.created",
        entity_type="teacher_assignment",
        entity_id=assignment.id,
        metadata_json={
            "teacher_id": assignment.teacher_id,
            "class_id": assignment.class_id,
            "section_id": assignment.section_id,
            "subject_id": assignment.subject_id,
        },
    )

    # Fetch loaded fields
    out = await list_teacher_assignments(db, school_id=school_id, teacher_id=data.teacher_id)
    for item in out:
        if item["id"] == assignment.id:
            return item
    return {"id": assignment.id, "school_id": school_id, **data.model_dump(), "created_at": assignment.created_at}


# ------------------- STUDENT ENROLLMENTS -------------------

async def list_student_enrollments(
    db: AsyncSession,
    school_id: str,
    class_id: Optional[str] = None,
    section_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    stmt = (
        select(StudentEnrollment)
        .options(
            selectinload(StudentEnrollment.student),
            selectinload(StudentEnrollment.class_obj),
            selectinload(StudentEnrollment.section),
        )
        .where(StudentEnrollment.school_id == school_id)
    )
    if class_id:
        stmt = stmt.where(StudentEnrollment.class_id == class_id)
    if section_id:
        stmt = stmt.where(StudentEnrollment.section_id == section_id)

    res = await db.execute(stmt)
    enrollments = res.scalars().all()

    output = []
    for e in enrollments:
        output.append({
            "id": e.id,
            "school_id": e.school_id,
            "student_id": e.student_id,
            "class_id": e.class_id,
            "section_id": e.section_id,
            "roll_number": e.roll_number,
            "status": e.status,
            "student_name": e.student.full_name if e.student else None,
            "class_name": e.class_obj.name if e.class_obj else None,
            "section_name": e.section.name if e.section else None,
            "created_at": e.created_at,
        })
    return output


async def create_student_enrollment(
    db: AsyncSession,
    school_id: str,
    data: StudentEnrollmentCreateRequest,
    actor_id: Optional[str] = None
) -> Dict[str, Any]:
    # Check duplicate
    dup_stmt = select(StudentEnrollment).where(
        StudentEnrollment.school_id == school_id,
        StudentEnrollment.student_id == data.student_id,
        StudentEnrollment.class_id == data.class_id,
        StudentEnrollment.section_id == data.section_id,
    )
    res_dup = await db.execute(dup_stmt)
    if res_dup.scalar_one_or_none():
        raise ConflictException("Student is already enrolled in this class and section")

    enrollment = StudentEnrollment(
        school_id=school_id,
        student_id=data.student_id,
        class_id=data.class_id,
        section_id=data.section_id,
        roll_number=data.roll_number,
        status="active",
    )
    db.add(enrollment)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="student_enrollment.created",
        entity_type="student_enrollment",
        entity_id=enrollment.id,
        metadata_json={
            "student_id": enrollment.student_id,
            "class_id": enrollment.class_id,
            "section_id": enrollment.section_id,
        },
    )

    out = await list_student_enrollments(db, school_id=school_id, class_id=data.class_id, section_id=data.section_id)
    for item in out:
        if item["id"] == enrollment.id:
            return item
    return {"id": enrollment.id, "school_id": school_id, **data.model_dump(), "status": "active", "created_at": enrollment.created_at}


# ------------------- CURRICULUM NODES -------------------

async def list_curriculum_nodes(
    db: AsyncSession,
    school_id: str,
    subject_id: Optional[str] = None,
    grade: Optional[str] = None
) -> List[CurriculumNode]:
    stmt = select(CurriculumNode).where(CurriculumNode.school_id == school_id)
    if subject_id:
        stmt = stmt.where(CurriculumNode.subject_id == subject_id)
    if grade:
        stmt = stmt.where(CurriculumNode.grade == grade)
    stmt = stmt.order_by(CurriculumNode.chapter, CurriculumNode.topic)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def create_curriculum_node(
    db: AsyncSession,
    school_id: str,
    data: CurriculumNodeCreateRequest,
    actor_id: Optional[str] = None
) -> CurriculumNode:
    node = CurriculumNode(
        school_id=school_id,
        subject_id=data.subject_id,
        grade=data.grade,
        board=data.board,
        chapter=data.chapter.strip(),
        topic=data.topic.strip(),
        learning_outcome=data.learning_outcome,
        source_ref=data.source_ref,
    )
    db.add(node)
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="curriculum_node.created",
        entity_type="curriculum_node",
        entity_id=node.id,
        metadata_json={"subject_id": node.subject_id, "chapter": node.chapter, "topic": node.topic},
    )

    return node


# ------------------- BULK EXCEL / CSV IMPORTER -------------------

async def process_bulk_import_file(
    db: AsyncSession,
    school_id: str,
    file_bytes: bytes,
    filename: str,
    actor_id: Optional[str] = None
) -> BulkImportResponse:
    """
    Parses and imports users, classes, sections, and assignments from Excel (.xlsx) or CSV.
    Role mapping preserves 3 canonical roles (Admin, Teacher, Student).
    Academic Coordinator is assigned role 'admin' with designation 'Academic Coordinator'.
    """
    rows: List[Dict[str, Any]] = []

    if filename.lower().endswith(".xlsx"):
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheet = wb.active
        headers = [str(cell.value or "").strip().lower() for cell in sheet[1]]
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if any(row):
                row_dict = {headers[i]: (str(val).strip() if val is not None else "") for i, val in enumerate(row) if i < len(headers)}
                rows.append({"row_number": row_idx, "data": row_dict})
    else:  # Assume CSV
        content = file_bytes.decode("utf-8-sig", errors="ignore")
        reader = csv.DictReader(io.StringIO(content))
        for row_idx, r in enumerate(reader, start=2):
            clean_dict = {k.strip().lower(): v.strip() for k, v in r.items() if k}
            rows.append({"row_number": row_idx, "data": clean_dict})

    # Fetch active academic year
    year_stmt = select(AcademicYear).where(AcademicYear.school_id == school_id, AcademicYear.status == "active").limit(1)
    res_year = await db.execute(year_stmt)
    active_year = res_year.scalar_one_or_none()
    if not active_year:
        # Fetch any year or create default
        y_all = select(AcademicYear).where(AcademicYear.school_id == school_id).limit(1)
        res_all = await db.execute(y_all)
        active_year = res_all.scalar_one_or_none()

    imported_count = 0
    errors: List[BulkImportRowError] = []

    for r in rows:
        row_num = r["row_number"]
        d = r["data"]

        email = d.get("email", "").lower().strip()
        full_name = d.get("full_name") or d.get("name", "").strip()
        raw_role = d.get("role", "").lower().strip()
        designation = d.get("designation") or d.get("post", "").strip()
        class_name = d.get("class") or d.get("class_name", "").strip()
        section_name = d.get("section") or d.get("section_name", "").strip()
        subject_code = d.get("subject") or d.get("subject_code", "").strip().upper()
        roll_number = d.get("roll_number", "").strip()

        if not email or not full_name:
            errors.append(BulkImportRowError(row_number=row_num, data=d, error="Missing required email or full_name"))
            continue

        # Map role according to 5-tier structure
        canonical_role = RoleName.STUDENT
        if "superadmin" in raw_role or "platform" in raw_role:
            canonical_role = RoleName.PLATFORM_ADMIN
        elif "admin" in raw_role or "principal" in raw_role or "head" in raw_role:
            canonical_role = RoleName.SCHOOL_ADMIN
        elif "coordinator" in raw_role:
            canonical_role = RoleName.ACADEMIC_COORDINATOR
            if not designation:
                designation = "Academic Coordinator"
        elif "teach" in raw_role or "faculty" in raw_role:
            canonical_role = RoleName.TEACHER
        elif "student" in raw_role:
            canonical_role = RoleName.STUDENT
        else:
            errors.append(BulkImportRowError(row_number=row_num, data=d, error=f"Unrecognized role '{raw_role}'"))
            continue

        try:
            # Check or create user
            u_stmt = select(User).where(User.school_id == school_id, User.email == email)
            u_res = await db.execute(u_stmt)
            user = u_res.scalar_one_or_none()

            if not user:
                user = User(
                    school_id=school_id,
                    email=email,
                    password_hash=hash_password("ChangeMe123!"),
                    full_name=full_name,
                    designation=designation or None,
                    status="active",
                    must_change_password=(canonical_role == RoleName.STUDENT),
                )
                db.add(user)
                await db.flush()

                role_asgn = RoleAssignment(
                    user_id=user.id,
                    role=canonical_role,
                    school_id=school_id,
                    status="active"
                )
                db.add(role_asgn)
                await db.flush()
                user.role_assignments.append(role_asgn)


            # Handle class and section if provided
            if class_name and active_year:
                c_stmt = select(Class).where(
                    Class.school_id == school_id,
                    Class.academic_year_id == active_year.id,
                    Class.name == class_name
                )
                c_res = await db.execute(c_stmt)
                class_obj = c_res.scalar_one_or_none()
                if not class_obj:
                    class_obj = Class(
                        school_id=school_id,
                        academic_year_id=active_year.id,
                        name=class_name
                    )
                    db.add(class_obj)
                    await db.flush()

                sec_obj = None
                if section_name:
                    sec_stmt = select(Section).where(Section.class_id == class_obj.id, Section.name == section_name)
                    sec_res = await db.execute(sec_stmt)
                    sec_obj = sec_res.scalar_one_or_none()
                    if not sec_obj:
                        sec_obj = Section(class_id=class_obj.id, name=section_name)
                        db.add(sec_obj)
                        await db.flush()

                # If student, enroll
                if canonical_role in (RoleName.STUDENT, "student") and sec_obj:
                    enr_stmt = select(StudentEnrollment).where(
                        StudentEnrollment.school_id == school_id,
                        StudentEnrollment.student_id == user.id,
                        StudentEnrollment.class_id == class_obj.id,
                        StudentEnrollment.section_id == sec_obj.id,
                    )
                    enr_res = await db.execute(enr_stmt)
                    if not enr_res.scalar_one_or_none():
                        enr = StudentEnrollment(
                            school_id=school_id,
                            student_id=user.id,
                            class_id=class_obj.id,
                            section_id=sec_obj.id,
                            roll_number=roll_number or None,
                            status="active",
                        )
                        db.add(enr)
                        await db.flush()

                # If teacher and subject given, assign
                if canonical_role in (RoleName.TEACHER, "teacher") and sec_obj and subject_code:
                    sub_stmt = select(Subject).where(Subject.school_id == school_id, Subject.code == subject_code)
                    sub_res = await db.execute(sub_stmt)
                    sub_obj = sub_res.scalar_one_or_none()
                    if not sub_obj:
                        sub_obj = Subject(school_id=school_id, name=subject_code, code=subject_code)
                        db.add(sub_obj)
                        await db.flush()

                    asgn_stmt = select(TeacherAssignment).where(
                        TeacherAssignment.school_id == school_id,
                        TeacherAssignment.teacher_id == user.id,
                        TeacherAssignment.class_id == class_obj.id,
                        TeacherAssignment.section_id == sec_obj.id,
                        TeacherAssignment.subject_id == sub_obj.id,
                    )
                    asgn_res = await db.execute(asgn_stmt)
                    if not asgn_res.scalar_one_or_none():
                        asgn = TeacherAssignment(
                            school_id=school_id,
                            teacher_id=user.id,
                            class_id=class_obj.id,
                            section_id=sec_obj.id,
                            subject_id=sub_obj.id,
                        )
                        db.add(asgn)
                        await db.flush()

            imported_count += 1

        except Exception as ex:
            errors.append(BulkImportRowError(row_number=row_num, data=d, error=str(ex)))

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="bulk_import.executed",
        entity_type="school",
        entity_id=school_id,
        metadata_json={"total": len(rows), "imported": imported_count, "errors": len(errors)},
    )

    return BulkImportResponse(
        success=len(errors) == 0,
        total_rows=len(rows),
        imported_count=imported_count,
        error_count=len(errors),
        errors=errors,
    )

