"""
Evaluation and Result Release Router
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.assessments import lifecycle_service

eval_router = APIRouter(tags=["Evaluation & Publishing"])


class PublishAssessmentRequest(BaseModel):
    starts_at: datetime
    ends_at: datetime
    timezone: str = "Asia/Kolkata"
    duration_minutes: Optional[int] = None
    max_attempts: int = 1
    allow_late_submission: bool = False
    result_release_mode: str = "manual_by_teacher"  # manual_by_teacher, immediate_on_submit, scheduled_datetime
    result_release_at: Optional[datetime] = None


class GradeResponseRequest(BaseModel):
    manual_score: float = Field(..., ge=0)
    teacher_feedback: Optional[str] = None


@eval_router.post("/assessments/{assessment_id}/publish")
async def publish_assessment_endpoint(
    assessment_id: str,
    payload: PublishAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment = await lifecycle_service.publish_or_schedule_assessment(
        db,
        school_id=current_user.school_id,
        assessment_id=assessment_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        timezone_str=payload.timezone,
        duration_minutes=payload.duration_minutes,
        max_attempts=payload.max_attempts,
        result_release_mode=payload.result_release_mode,
        result_release_at=payload.result_release_at,
        allow_late_submission=payload.allow_late_submission,
        actor_id=current_user.id,
    )
    return {
        "assessment_id": assessment.id,
        "status": assessment.status,
        "starts_at": payload.starts_at,
        "ends_at": payload.ends_at,
        "release_mode": payload.result_release_mode,
    }


@eval_router.get("/teacher/evaluation-queue")
async def get_evaluation_queue_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lifecycle_service.get_teacher_evaluation_queue(
        db, school_id=current_user.school_id, teacher_id=current_user.id
    )


@eval_router.patch("/evaluations/{response_id}")
async def grade_response_endpoint(
    response_id: str,
    payload: GradeResponseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resp = await lifecycle_service.grade_student_response(
        db,
        school_id=current_user.school_id,
        response_id=response_id,
        teacher_id=current_user.id,
        manual_score=payload.manual_score,
        teacher_feedback=payload.teacher_feedback,
    )
    return {
        "response_id": resp.id,
        "manual_score": resp.manual_score,
        "teacher_feedback": resp.teacher_feedback,
    }


@eval_router.post("/assessments/{assessment_id}/release-results")
async def release_results_endpoint(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await lifecycle_service.release_assessment_results(
        db,
        school_id=current_user.school_id,
        assessment_id=assessment_id,
        actor_id=current_user.id,
    )
    return {
        "assessment_id": assessment_id,
        "released_attempts": count,
        "status": "results_released",
    }

