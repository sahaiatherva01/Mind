"""
Academic Schemas: Classes, Sections, Subjects, Assignments, Enrollments, Curriculum, Bulk Import
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class SectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=20)  # e.g., "A", "E", "D"


class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    class_id: str
    name: str
    created_at: datetime


class ClassCreateRequest(BaseModel):
    academic_year_id: str
    name: str = Field(..., min_length=1, max_length=50)  # e.g., "Class 11", "Class 12"
    band_id: Optional[str] = None
    grade_level: Optional[int] = None
    section_names: Optional[List[str]] = None  # e.g., ["A", "E", "D"]


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    academic_year_id: str
    name: str
    band_id: Optional[str] = None
    grade_level: Optional[int] = None
    sections: List[SectionResponse] = []
    created_at: datetime


class SubjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    name: str
    code: str
    created_at: datetime


class TeacherAssignmentCreateRequest(BaseModel):
    teacher_id: str
    class_id: str
    section_id: str
    subject_id: str
    academic_year_id: Optional[str] = None
    is_class_teacher: bool = False
    status: str = "active"


class TeacherAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    teacher_id: str
    class_id: str
    section_id: str
    subject_id: str
    academic_year_id: Optional[str] = None
    is_class_teacher: bool = False
    status: str = "active"
    teacher_name: Optional[str] = None
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    subject_name: Optional[str] = None
    created_at: datetime


class StudentEnrollmentCreateRequest(BaseModel):
    student_id: str
    class_id: str
    section_id: str
    roll_number: Optional[str] = None


class StudentEnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    student_id: str
    class_id: str
    section_id: str
    roll_number: Optional[str] = None
    status: str
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    created_at: datetime


class CurriculumNodeCreateRequest(BaseModel):
    subject_id: str
    grade: str
    board: str = "ICSE/ISC"
    chapter: str
    topic: str
    learning_outcome: Optional[str] = None
    source_ref: Optional[str] = None


class CurriculumNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    subject_id: str
    grade: str
    board: str
    chapter: str
    topic: str
    learning_outcome: Optional[str] = None
    source_ref: Optional[str] = None
    created_at: datetime


class BulkImportRowError(BaseModel):
    row_number: int
    data: Dict[str, Any]
    error: str


class BulkImportResponse(BaseModel):
    success: bool
    total_rows: int
    imported_count: int
    error_count: int
    errors: List[BulkImportRowError] = []


class AssignmentMatrixItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    teacher_id: str
    teacher_name: str
    teacher_email: str
    class_id: str
    class_name: str
    section_id: str
    section_name: str
    subject_id: str
    subject_name: str
    subject_code: str
    is_class_teacher: bool = False
    status: str = "active"


class ClassTeacherDesignateRequest(BaseModel):
    section_id: str
    teacher_id: str
    academic_year_id: Optional[str] = None


class CoordinatorTeacherCreateRequest(BaseModel):
    email: str
    full_name: str
    password: Optional[str] = "TeacherPass123!"
    designation: Optional[str] = "PGT / TGT Faculty"
    class_id: str
    section_id: str
    subject_id: str
    is_class_teacher: bool = False


class BandSummaryResponse(BaseModel):
    band_id: str
    band_name: str
    min_grade: int
    max_grade: int
    classes: List[ClassResponse]
    total_classes: int
    total_sections: int
    total_teachers: int
    total_students: int
    class_teachers: Dict[str, Optional[str]] = {}  # section_id -> teacher_name
