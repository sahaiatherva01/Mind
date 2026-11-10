"""
Student Assessment Router: Assignments, Attempt Player, Resilient Autosave, and Submissions
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.assessments import lifecycle_service

student_router = APIRouter(prefix="/student", tags=["Student Assessments"])
attempts_router = APIRouter(prefix="/attempts", tags=["Assessment Attempts"])
asmt_delivery_router = APIRouter(prefix="/assessments", tags=["Assessment Delivery"])


class AutosavePayload(BaseModel):
    answer_json: Dict[str, Any]


class ExamTelemetryPayload(BaseModel):
    event_type: str  # "tab_switch", "fullscreen_exit", "offline_reconnect"
    details: Optional[Dict[str, Any]] = None


@student_router.get("/assignments")
async def get_my_assignments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lifecycle_service.list_student_assignments(
        db, school_id=current_user.school_id, student_id=current_user.id
    )


@asmt_delivery_router.get("/{assessment_id}/instructions")
async def get_assessment_instructions(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lifecycle_service.get_student_assessment_instructions(
        db, school_id=current_user.school_id, assessment_id=assessment_id, student_id=current_user.id
    )


@asmt_delivery_router.post("/{assessment_id}/attempts", status_code=status.HTTP_201_CREATED)
async def start_assessment_attempt(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attempt, safe_questions = await lifecycle_service.start_student_attempt(
        db, school_id=current_user.school_id, assessment_id=assessment_id, student_id=current_user.id
    )
    return {
        "attempt_id": attempt.id,
        "started_at": attempt.started_at,
        "max_score": attempt.max_score,
        "questions": safe_questions,
    }


@attempts_router.put("/{attempt_id}/responses/{item_id}")
async def autosave_response_endpoint(
    attempt_id: str,
    item_id: str,
    payload: AutosavePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resp = await lifecycle_service.autosave_student_response(
        db,
        school_id=current_user.school_id,
        attempt_id=attempt_id,
        item_id=item_id,
        student_id=current_user.id,
        answer_json=payload.answer_json,
    )
    return {
        "status": "saved",
        "saved_at": resp.saved_at,
        "item_id": item_id,
    }


@attempts_router.post("/{attempt_id}/submit")
async def submit_attempt_endpoint(
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attempt = await lifecycle_service.submit_student_attempt(
        db,
        school_id=current_user.school_id,
        attempt_id=attempt_id,
        student_id=current_user.id,
    )
    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "submitted_at": attempt.submitted_at,
        "is_released": attempt.is_released,
        "auto_score": attempt.total_score if attempt.is_released else None,
    }


@attempts_router.get("/{attempt_id}/results")
async def get_attempt_results_endpoint(
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lifecycle_service.get_student_attempt_result(
        db,
        school_id=current_user.school_id,
        attempt_id=attempt_id,
        student_id=current_user.id,
    )


@attempts_router.post("/{attempt_id}/telemetry")
async def record_attempt_telemetry_endpoint(
    attempt_id: str,
    payload: ExamTelemetryPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logs anti-cheat telemetry: tab switches, fullscreen departures, and offline recovery."""
    from datetime import datetime, timezone
    from backend.app.assessments.models import Attempt
    from backend.app.core.errors import ForbiddenException, NotFoundException

    attempt = await db.get(Attempt, attempt_id)
    if not attempt or attempt.student_id != current_user.id:
        raise ForbiddenException("Access denied to this attempt telemetry.")

    if payload.event_type == "tab_switch":
        attempt.tab_switches_count += 1

    events = list(attempt.integrity_events_json or [])
    events.append({
        "event_type": payload.event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": payload.details or {},
    })
    attempt.integrity_events_json = events
    await db.flush()

    return {
        "status": "recorded",
        "tab_switches_count": attempt.tab_switches_count,
        "total_integrity_events": len(events),
    }

