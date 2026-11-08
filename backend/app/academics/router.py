"""
Academics Router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.academics import service, policies
from backend.app.academics.schemas import (
    ClassResponse,
    ClassCreateRequest,
    SectionResponse,
    SectionCreateRequest,
    SubjectResponse,
    SubjectCreateRequest,
    TeacherAssignmentResponse,
    TeacherAssignmentCreateRequest,
    StudentEnrollmentResponse,
    StudentEnrollmentCreateRequest,
    CurriculumNodeResponse,
    CurriculumNodeCreateRequest,
    BulkImportResponse,
)

classes_router = APIRouter(prefix="/classes", tags=["Classes"])
subjects_router = APIRouter(prefix="/subjects", tags=["Subjects"])
assignments_router = APIRouter(prefix="/teacher-assignments", tags=["Teacher Assignments"])
enrollments_router = APIRouter(prefix="/student-enrollments", tags=["Student Enrollments"])
curriculum_router = APIRouter(prefix="/curriculum", tags=["Curriculum"])
academics_router = APIRouter(prefix="/academics", tags=["Academic Operations"])


# --- CLASSES & SECTIONS ---

@classes_router.get("", response_model=List[ClassResponse])
async def list_classes_endpoint(
    academic_year_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    classes = await service.list_classes(db, current_user.school_id, academic_year_id=academic_year_id)
    return [ClassResponse.model_validate(c) for c in classes]


@classes_router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class_endpoint(
    payload: ClassCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_academic_setup(current_user)
    new_class = await service.create_class(
        db=db,
        school_id=current_user.school_id,
        data=payload,
        actor_id=current_user.id
    )
    return ClassResponse.model_validate(new_class)


@classes_router.post("/{class_id}/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section_endpoint(
    class_id: str,
    payload: SectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_academic_setup(current_user)
    section = await service.create_section(
        db=db,
        class_id=class_id,
        data=payload,
        school_id=current_user.school_id,
        actor_id=current_user.id
    )
    return SectionResponse.model_validate(section)


# --- SUBJECTS ---

@subjects_router.get("", response_model=List[SubjectResponse])
async def list_subjects_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subjects = await service.list_subjects(db, current_user.school_id)
    return [SubjectResponse.model_validate(s) for s in subjects]


@subjects_router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject_endpoint(
    payload: SubjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_academic_setup(current_user)
    subject = await service.create_subject(
        db=db,
        school_id=current_user.school_id,
        data=payload,
        actor_id=current_user.id
    )
    return SubjectResponse.model_validate(subject)


# --- TEACHER ASSIGNMENTS ---

@assignments_router.get("", response_model=List[TeacherAssignmentResponse])
async def list_assignments_endpoint(
    teacher_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # If teacher role, limit to self
    target_teacher_id = current_user.id if current_user.role == "teacher" else teacher_id
    assignments = await service.list_teacher_assignments(db, current_user.school_id, teacher_id=target_teacher_id)
    return [TeacherAssignmentResponse.model_validate(a) for a in assignments]


@assignments_router.post("", response_model=TeacherAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment_endpoint(
    payload: TeacherAssignmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_academic_setup(current_user)
    res = await service.create_teacher_assignment(
        db=db,
        school_id=current_user.school_id,
        data=payload,
        actor_id=current_user.id
    )
    return TeacherAssignmentResponse.model_validate(res)


# --- STUDENT ENROLLMENTS ---

@enrollments_router.get("", response_model=List[StudentEnrollmentResponse])
async def list_enrollments_endpoint(
    class_id: Optional[str] = Query(None),
    section_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enrollments = await service.list_student_enrollments(
        db, current_user.school_id, class_id=class_id, section_id=section_id
    )
    return [StudentEnrollmentResponse.model_validate(e) for e in enrollments]


@enrollments_router.post("", response_model=StudentEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def create_enrollment_endpoint(
    payload: StudentEnrollmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_academic_setup(current_user)
    res = await service.create_student_enrollment(
        db=db,
        school_id=current_user.school_id,
        data=payload,
        actor_id=current_user.id
    )
    return StudentEnrollmentResponse.model_validate(res)


# --- CURRICULUM ---

@curriculum_router.get("", response_model=List[CurriculumNodeResponse])
async def list_curriculum_endpoint(
    subject_id: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    nodes = await service.list_curriculum_nodes(
        db, current_user.school_id, subject_id=subject_id, grade=grade
    )
    return [CurriculumNodeResponse.model_validate(n) for n in nodes]


@curriculum_router.post("", response_model=CurriculumNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_curriculum_node_endpoint(
    payload: CurriculumNodeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_academic_setup(current_user)
    node = await service.create_curriculum_node(
        db=db,
        school_id=current_user.school_id,
        data=payload,
        actor_id=current_user.id
    )
    return CurriculumNodeResponse.model_validate(node)


# --- BULK IMPORT ---

@academics_router.post("/bulk-import", response_model=BulkImportResponse)
async def bulk_import_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies.can_manage_academic_setup(current_user)
    content = await file.read()
    res = await service.process_bulk_import_file(
        db=db,
        school_id=current_user.school_id,
        file_bytes=content,
        filename=file.filename or "import.csv",
        actor_id=current_user.id,
    )
    return res

