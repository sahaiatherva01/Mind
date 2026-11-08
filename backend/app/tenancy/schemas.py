"""
Tenancy Schemas: Schools and Academic Years
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class SchoolCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    timezone: str = "Asia/Kolkata"
    settings: Optional[Dict[str, Any]] = None


class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    timezone: str
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime


class AcademicYearCreateRequest(BaseModel):
    label: str = Field(..., min_length=2, max_length=50)  # e.g., "2026-2027"
    starts_on: date
    ends_on: date
    status: str = Field("active", pattern="^(active|archived|upcoming)$")


class AcademicYearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    label: str
    starts_on: date
    ends_on: date
    status: str
    created_at: datetime
