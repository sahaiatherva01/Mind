"""
Tenancy Schemas: Schools, Bands, Academic Years, and Platform Administration — Mind V2
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class BandCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)  # e.g., "Secondary (9-10)"
    min_grade: int = Field(..., ge=1, le=12)
    max_grade: int = Field(..., ge=1, le=12)


class BandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    name: str
    min_grade: int
    max_grade: int
    created_at: datetime


class SchoolCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    board: Optional[str] = Field("ICSE/ISC", max_length=50)
    timezone: str = "Asia/Kolkata"
    academic_year_label: Optional[str] = "2026-2027"
    settings: Optional[Dict[str, Any]] = None


class SchoolUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    board: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|suspended|archived)$")
    settings: Optional[Dict[str, Any]] = None


class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    code: Optional[str] = None
    board: Optional[str] = "ICSE/ISC"
    status: str = "active"
    timezone: str = "Asia/Kolkata"
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


class PlatformDashboardResponse(BaseModel):
    total_schools: int
    total_users: int
    active_users: int
    total_assessments: int


class FeatureFlagUpdateRequest(BaseModel):
    flags: Dict[str, bool]


class SchoolAdminCreateRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    designation: Optional[str] = "School Administrator"


class CoordinatorCreateRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    band_id: str
    designation: Optional[str] = "Academic Coordinator"
