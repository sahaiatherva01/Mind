"""
Exams, Calendar, Blueprints & Report Cards Router — Mind V2
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.exams.schemas import (
    CalendarEventCreate,
    CalendarEventResponse,
    ClashCheckRequest,
    ClashCheckResponse,
    ExamBlueprintCreate,
    ExamBlueprintResponse,
    StudentReportCardResponse,
    SectionGradebookResponse,
)
from backend.app.exams.service import ExamCalendarService

router = APIRouter(tags=["Exams & Academic Calendar"])


# --- Academic Calendar & Clash Detection ---

@router.post("/calendar/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    payload: CalendarEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a school, band, or class calendar event (blackout window, holiday, exam period)."""
    return await ExamCalendarService.create_calendar_event(db, current_user, payload)


@router.get("/calendar/events", response_model=List[CalendarEventResponse])
async def list_calendar_events(
    band_id: Optional[str] = None,
    class_id: Optional[str] = None,
    section_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List calendar events within user's authorized scope."""
    return await ExamCalendarService.list_calendar_events(db, current_user, band_id, class_id, section_id)


@router.post("/calendar/check-clash", response_model=ClashCheckResponse)
async def check_calendar_clash(
    payload: ClashCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check assessment schedule slot against blackout periods and max 2 assessments/day policy limit."""
    return await ExamCalendarService.check_schedule_clash(db, current_user, payload)


# --- Band-Wide Exam Blueprints & Multi-Set A-D ---

@router.post("/exams/blueprints", response_model=ExamBlueprintResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_blueprint(
    payload: ExamBlueprintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Define a band-wide exam blueprint specification."""
    return await ExamCalendarService.create_exam_blueprint(db, current_user, payload)


@router.get("/exams/blueprints", response_model=List[ExamBlueprintResponse])
async def list_exam_blueprints(
    band_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List exam blueprints for band coordinator or school admin."""
    return await ExamCalendarService.list_exam_blueprints(db, current_user, band_id)


@router.post("/exams/blueprints/{blueprint_id}/generate-sets", response_model=ExamBlueprintResponse)
async def generate_multiset_exam(
    blueprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate Sets A, B, C, D with parallel item distributions from common blueprint."""
    return await ExamCalendarService.generate_multiset_exam(db, current_user, blueprint_id)


@router.post("/exams/blueprints/{blueprint_id}/approve", response_model=ExamBlueprintResponse)
async def approve_exam_blueprint(
    blueprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Academic Coordinator approves generated exam blueprint and multi-set papers."""
    return await ExamCalendarService.approve_exam_blueprint(db, current_user, blueprint_id)


# --- Branded Report Cards & Gradebook ---

@router.get("/reports/student/{student_id}/report-card", response_model=StudentReportCardResponse)
async def get_student_report_card(
    student_id: str,
    term: str = "Term 1",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate official academic report card with term grades, co-scholastic remarks & attendance."""
    return await ExamCalendarService.generate_student_report_card(db, current_user, student_id, term)


@router.get("/reports/sections/{section_id}/gradebook", response_model=SectionGradebookResponse)
async def get_section_gradebook(
    section_id: str,
    term: str = "Term 1",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate section gradebook matrix across all enrolled students."""
    return await ExamCalendarService.generate_section_gradebook(db, current_user, section_id, term)
