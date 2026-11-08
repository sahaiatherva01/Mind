"""
Generation Request & Response Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field
from ai_engine.schemas.question import QuestionType, DifficultyLevel, CanonicalQuestion


class GenerationBaseRequest(BaseModel):
    class_id: str
    section_id: str
    subject_id: str
    chapter: str = Field(..., min_length=2)
    topics: List[str] = Field(..., min_length=1)
    difficulty: Dict[DifficultyLevel, int] = {"easy": 30, "medium": 50, "hard": 20}
    question_count: int = Field(10, ge=1, le=50)
    total_marks: int = Field(20, ge=1, le=100)
    language: str = "en"
    instructions: Optional[str] = None
    board: str = "ICSE/ISC"


class WorksheetGenerateRequest(GenerationBaseRequest):
    question_types: List[QuestionType] = ["short_answer", "numerical_based", "reasoning_based"]


class QuizGenerateRequest(GenerationBaseRequest):
    question_types: List[QuestionType] = ["mcq", "fill_in_the_blanks", "assertion_reason"]


class QuestionPaperGenerateRequest(GenerationBaseRequest):
    question_types: List[QuestionType] = [
        "mcq",
        "short_answer",
        "numerical_based",
        "proof_derivation_based",
        "hots"
    ]
    sections_layout: Optional[Dict[str, Any]] = None  # Section A (Objective), Section B (Subjective)


class CustomQuestionGenerateRequest(GenerationBaseRequest):
    question_types: List[QuestionType] = ["mcq", "short_answer"]


class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime


class JobDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    model: str
    warnings: Optional[List[str]] = []
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    assessment_id: Optional[str] = None
    questions: Optional[List[CanonicalQuestion]] = None
    created_at: datetime
