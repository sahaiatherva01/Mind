"""
Pydantic Schemas for Exams, Calendar, Multi-Set Blueprints & Report Cards — Mind V2
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# --- Calendar Schemas ---

class CalendarEventCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    event_type: str = Field(..., pattern="^(blackout|exam_period|holiday|event|assessment)$")
    starts_at: datetime
    ends_at: datetime
    description: Optional[str] = None
    academic_year_id: Optional[str] = None
    band_id: Optional[str] = None
    class_id: Optional[str] = None
    section_id: Optional[str] = None


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    title: str
    event_type: str
    starts_at: datetime
    ends_at: datetime
    description: Optional[str] = None
    academic_year_id: Optional[str] = None
    band_id: Optional[str] = None
    class_id: Optional[str] = None
    section_id: Optional[str] = None
    created_by: str


class ClashCheckRequest(BaseModel):
    section_id: str
    starts_at: datetime
    ends_at: datetime
    assessment_id: Optional[str] = None


class ClashCheckResponse(BaseModel):
    has_clash: bool
    clash_type: str  # "policy_limit" (max 2/day), "blackout", "none"
    message: str
    conflicting_events: List[Dict[str, Any]] = []


# --- Exam Blueprint & Multi-Set Schemas ---

class BlueprintStructureSection(BaseModel):
    section_name: str  # e.g. "Section A - Objective"
    question_type: str  # mcq, short_answer, etc.
    count: int
    marks_per_question: float


class ExamBlueprintCreate(BaseModel):
    band_id: str
    subject_id: str
    academic_year_id: Optional[str] = None
    title: str = Field(..., min_length=3, max_length=255)
    total_marks: float = Field(..., gt=0)
    duration_minutes: int = Field(default=180, gt=0)
    term: str = "Term 1"
    sections: List[BlueprintStructureSection]
    topics: List[str]
    difficulty_ratio: Dict[str, float] = Field(
        default_factory=lambda: {"easy": 0.3, "medium": 0.5, "hard": 0.2}
    )


class ExamSetItem(BaseModel):
    prompt: str
    type: str
    marks: float
    topic: str
    difficulty: str


class ExamSetData(BaseModel):
    set_label: str  # "Set A", "Set B", "Set C", "Set D"
    title: str
    items_count: int
    total_marks: float
    items: List[Dict[str, Any]]


class ExamBlueprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    band_id: str
    subject_id: str
    title: str
    total_marks: float
    duration_minutes: int
    term: str
    status: str
    structure_json: Dict[str, Any]
    sets_data_json: List[Dict[str, Any]]
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


# --- Report Card & Gradebook Schemas ---

class SubjectGradeReport(BaseModel):
    subject_id: str
    subject_name: str
    total_max_marks: float
    obtained_marks: float
    percentage: float
    grade: str
    remarks: str


class StudentReportCardResponse(BaseModel):
    school_id: str
    school_name: str
    student_id: str
    student_name: str
    roll_number: Optional[str] = None
    class_name: str
    section_name: str
    term: str
    academic_year: str
    subjects: List[SubjectGradeReport]
    total_possible_marks: float
    total_obtained_marks: float
    overall_percentage: float
    overall_grade: str
    attendance_pct: float
    teacher_general_remarks: str


class SectionGradebookResponse(BaseModel):
    school_id: str
    class_id: str
    class_name: str
    section_id: str
    section_name: str
    term: str
    students: List[Dict[str, Any]]
    section_average_pct: float


# --- Subjective Evaluation Assistant Schemas (Track A3) ---

class EvaluationAssistRequest(BaseModel):
    response_id: str


class EvaluationAssistResponse(BaseModel):
    response_id: str
    question_prompt: str
    student_answer_text: str
    model_answer: Optional[str] = None
    max_marks: float
    suggested_score: float
    step_breakdown: List[Dict[str, Any]]
    teacher_feedback_note: str
    confidence_score: float

