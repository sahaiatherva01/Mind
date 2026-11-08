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
    section_names: Optional[List[str]] = None  # e.g., ["A", "E", "D"]


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    academic_year_id: str
    name: str
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


class TeacherAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    teacher_id: str
    class_id: str
    section_id: str
    subject_id: str
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
