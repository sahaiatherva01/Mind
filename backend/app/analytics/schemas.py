"""
Pydantic Schemas for 4-Level Analytics, Cross-Analytics, and AI Diagnostic Insights
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class QuestionAnalysis(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_id: str
    item_type: str
    prompt: str
    max_marks: float
    topic: Optional[str] = None
    total_responses: int
    correct_responses: int
    average_marks_awarded: float
    accuracy_pct: float
    discrimination_index: float
    interpretation: str


class AssessmentAnalytics(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    assessment_id: str
    title: str
    subject: str
    total_enrolled: int
    submitted_count: int
    total_max_marks: float
    average_score: float
    average_score_pct: float
    median_score: float
    highest_score: float
    lowest_score: float
    score_distribution: Dict[str, int]
    question_analysis: List[QuestionAnalysis]


class ClassAssessmentSummary(BaseModel):
    assessment_id: str
    title: str
    subject: str
    submitted_count: int
    average_score_pct: float
    status: str


class ClassAnalytics(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    class_id: str
    class_name: str
    total_students: int
    total_assessments: int
    total_attempts: int
    average_score_pct: float
    completion_rate_pct: float
    assessments: List[ClassAssessmentSummary]


class TopicMastery(BaseModel):
    topic: str
    subject: str
    total_items: int
    total_attempts: int
    average_mastery_pct: float
    status: str  # "mastered", "proficient", "needs_reinforcement"


class TeacherDashboardSummary(BaseModel):
    assigned_classes_count: int
    active_assessments_count: int
    pending_evaluations_count: int
    total_graded_submissions: int


# --- Phase 6: Extended Multi-Level Analytics Schemas ---

class SchoolAnalyticsSummary(BaseModel):
    total_students: int
    total_teachers: int
    total_classes: int
    total_assessments: int
    school_average_pct: float
    overall_pass_pct: float
    term_trends: List[Dict[str, Any]]
    grade_distribution: Dict[str, int]
    teacher_activity: List[Dict[str, Any]]


class BandAnalyticsSummary(BaseModel):
    band_id: str
    band_name: str
    total_classes: int
    total_sections: int
    total_students: int
    total_assessments: int
    band_average_pct: float
    at_risk_students_count: int
    section_comparisons: List[Dict[str, Any]]
    syllabus_coverage: List[Dict[str, Any]]


class IndividualStudentAnalytics(BaseModel):
    student_id: str
    student_name: str
    roll_number: Optional[str] = None
    class_name: str
    section_name: str
    average_score_pct: float
    submission_rate_pct: float
    marks_trend: List[Dict[str, Any]]
    topic_strengths: List[TopicMastery]
    materials_read_count: int
    reading_duration_minutes: float


class TeacherFourLevelAnalytics(BaseModel):
    class_level: Dict[str, Any]
    subject_level: Dict[str, Any]
    cross_analytics: Dict[str, Any]
    individual_student: Optional[IndividualStudentAnalytics] = None


class StudentPerformanceMap(BaseModel):
    student_id: str
    student_name: str
    class_name: str
    section_name: str
    total_assessments_taken: int
    average_score_pct: float
    topic_mastery: List[TopicMastery]
    materials_completed_count: int


# --- Agent Track A5: Analytics Insight Agent Schemas ---

class AnalyticsInsightRequest(BaseModel):
    scope_type: Literal["school", "band", "class", "subject", "student"]
    scope_id: Optional[str] = None


class AnalyticsInsightResponse(BaseModel):
    scope_type: str
    scope_id: Optional[str] = None
    summary: str
    strengths: List[str]
    conceptual_gaps: List[str]
    pedagogical_recommendations: List[str]
    evidence_tools_used: List[str]
