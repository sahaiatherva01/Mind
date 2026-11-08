from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict


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
