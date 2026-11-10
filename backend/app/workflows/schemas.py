"""
Pydantic Schemas for Advanced Workflows — Mind V2 (Phase 8)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# --- Early Warnings & Coordinator Interventions ---

class EarlyWarningSignal(BaseModel):
    student_id: str
    student_name: str
    roll_number: Optional[str] = None
    class_name: str
    section_name: str
    average_score_pct: float
    risk_factors: List[str]
    severity: str  # "medium", "high", "critical"


class InterventionCreate(BaseModel):
    band_id: str
    student_id: str
    trigger_reason: str = Field(..., min_length=5, max_length=500)
    severity: str = "medium"  # low, medium, high, critical
    notes: Optional[str] = None


class InterventionUpdate(BaseModel):
    status: Optional[str] = None  # open, in_progress, resolved
    action_taken: Optional[str] = None
    notes: Optional[str] = None


class InterventionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    band_id: str
    student_id: str
    student_name: Optional[str] = None
    trigger_reason: str
    severity: str
    status: str
    action_taken: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


# --- Smart Student Groups & Remedial Generation ---

class SmartGroupCreate(BaseModel):
    class_id: str
    section_id: str
    subject_id: str
    name: str = Field(..., min_length=2, max_length=255)
    group_type: str = "remedial"  # remedial, core, advanced
    student_ids: List[str]
    weak_topics: List[str] = Field(default_factory=list)


class SmartGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    class_id: str
    section_id: str
    subject_id: str
    name: str
    group_type: str
    student_ids_json: List[str]
    weak_topics_json: List[str]
    created_at: datetime


class RemedialGenerationResponse(BaseModel):
    group_id: str
    group_name: str
    assessment_id: str
    title: str
    weak_topics: List[str]
    status: str  # "draft" / "needs_review"
    questions_count: int


# --- Substitution Manager ---

class SubstituteTeacherAssignRequest(BaseModel):
    teacher_id: str
    class_id: str
    section_id: str
    subject_id: str
    valid_from: datetime
    valid_to: datetime
    reason: Optional[str] = None


class SubstituteTeacherResponse(BaseModel):
    assignment_id: str
    teacher_id: str
    teacher_name: str
    class_name: str
    section_name: str
    subject_name: str
    is_substitute: bool
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


# --- Student Goals & Doubts ---

class StudentGoalCreate(BaseModel):
    subject_id: str
    target_score_pct: float = Field(..., ge=0, le=100)
    target_date: Optional[datetime] = None
    notes: Optional[str] = None


class StudentGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    subject_id: str
    subject_name: str
    target_score_pct: float
    current_score_pct: float
    status: str
    target_date: Optional[datetime] = None
    notes: Optional[str] = None


class StudentDoubtCreate(BaseModel):
    subject_id: str
    question_id: Optional[str] = None
    query_text: str = Field(..., min_length=5, max_length=2000)


class DoubtAnswerRequest(BaseModel):
    response_text: str = Field(..., min_length=2, max_length=2000)


class StudentDoubtResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    student_name: str
    teacher_id: str
    teacher_name: str
    subject_id: str
    subject_name: str
    question_id: Optional[str] = None
    query_text: str
    status: str
    response_text: Optional[str] = None
    created_at: datetime
    responded_at: Optional[datetime] = None


class RevisionItem(BaseModel):
    question_id: str
    prompt: str
    topic: str
    difficulty: str
    marks: float
    last_attempt_score: float
    suggested_action: str

