"""
Identity Schemas: Authentication, Users, and Me Endpoints
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: str
    school_id: str
    email: str
    full_name: str
    role: str
    designation: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    user: UserResponse
    session_token: str
    expires_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token_dev: Optional[str] = None  # Returned only in development/test environments


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    role: str = Field(..., pattern="^(admin|teacher|student)$")
    designation: Optional[str] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")


class SchoolSummaryResponse(BaseModel):
    id: str
    name: str
    slug: str
    timezone: str

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    user: UserResponse
    school: SchoolSummaryResponse
    active_academic_year_id: Optional[str] = None
