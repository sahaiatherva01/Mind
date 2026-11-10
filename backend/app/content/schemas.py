"""
Pydantic Schemas for Materials, Distribution, Engagement and Question Extraction
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MaterialCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    file_url: str = Field(..., min_length=1, max_length=1000)
    file_type: str = Field("application/pdf", max_length=50)
    file_size_bytes: int = Field(0, ge=0)
    subject_id: str
    class_id: str
    chapter: Optional[str] = Field(None, max_length=255)
    topic: Optional[str] = Field(None, max_length=255)
    content_text: Optional[str] = None
    target_section_ids: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class MaterialDistributionUpdate(BaseModel):
    target_section_ids: List[str] = Field(..., min_items=1)


class MaterialOut(BaseModel):
    id: str
    school_id: str
    uploader_id: str
    subject_id: str
    class_id: str
    subject_name: Optional[str] = None
    class_name: Optional[str] = None
    title: str
    description: Optional[str]
    file_url: str
    file_type: str
    file_size_bytes: int
    chapter: Optional[str]
    topic: Optional[str]
    status: str
    created_at: datetime
    distributed_section_ids: List[str] = []
    distributed_section_names: List[str] = []
    open_count: int = 0
    unique_readers_count: int = 0


class StudentMaterialOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    file_url: str
    file_type: str
    file_size_bytes: int
    subject_id: str
    subject_name: str
    class_id: str
    class_name: str
    chapter: Optional[str]
    topic: Optional[str]
    content_text: Optional[str] = None
    created_at: datetime
    has_opened: bool = False
    last_opened_at: Optional[datetime] = None


class MaterialOpenPayload(BaseModel):
    duration_seconds: int = Field(0, ge=0)
    pages_read: int = Field(1, ge=1)


class QuestionExtractionRequest(BaseModel):
    max_questions: int = Field(5, ge=1, le=20)


class QuestionApprovalRequest(BaseModel):
    candidate_question_id: str
    prompt: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    marks: Optional[int] = None
    difficulty: Optional[str] = None
    expected_answer: Optional[str] = None
    marking_scheme: Optional[str] = None
    options: Optional[List[Dict[str, Any]]] = None
    answer_keys: Optional[List[str]] = None
