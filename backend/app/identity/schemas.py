"""
Identity Schemas: Authentication, Users, and Me Endpoints — Mind V2
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=6)


class RoleAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    school_id: Optional[str] = None
    band_id: Optional[str] = None
    status: str
    effective_from: datetime
    effective_to: Optional[datetime] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: Optional[str] = None
    email: str
    full_name: str
    role: str
    designation: Optional[str] = None
    status: str
    must_change_password: bool = False
    created_at: datetime
    role_assignments: List[RoleAssignmentResponse] = []


class LoginResponse(BaseModel):
    user: UserResponse
    session_token: str
    expires_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token_dev: Optional[str] = None  # Returned only in development/test environments


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)


class UserCreateRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    role: str = Field(
        ...,
        pattern="^(platform_admin|school_admin|academic_coordinator|teacher|student|admin)$"
    )
    band_id: Optional[str] = None
    designation: Optional[str] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")


class SchoolSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    timezone: str


class MeResponse(BaseModel):
    user: UserResponse
    school: Optional[SchoolSummaryResponse] = None
    active_academic_year_id: Optional[str] = None
