"""
Assessment Schemas for Authoring, Review, and Approval
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class QuestionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    type: str
    prompt: str
    marks: int
    difficulty: str
    topic_tags: Optional[List[str]] = []
    content_data: Dict[str, Any] = {}
    # Answer data included for teacher review
    answer_data: Optional[Dict[str, Any]] = None
    version: int


class AssessmentItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    position: int
    marks_override: Optional[int] = None
    question: QuestionItemResponse


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    creator_id: str
    class_id: str
    section_id: str
    subject_id: str
    title: str
    type: str
    status: str
    version: int
    total_marks: int
    instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}
    items: List[AssessmentItemDetailResponse] = []
    created_at: datetime
    updated_at: datetime


class AssessmentItemUpdateRequest(BaseModel):
    prompt: Optional[str] = None
    marks: Optional[int] = Field(None, ge=1, le=100)
    position: Optional[int] = None
    options: Optional[List[Dict[str, Any]]] = None
    expected_answer: Optional[str] = None


class AssessmentUpdateRequest(BaseModel):
    title: Optional[str] = None
    instructions: Optional[str] = None


class ItemRegenerateRequest(BaseModel):
    feedback: str = Field(..., min_length=2)
