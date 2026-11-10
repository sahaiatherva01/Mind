"""
Roster & Student Credential Router — Mind V2
Base Path: /api/v1/rosters
Endpoints for Class Teacher student onboarding, roster lifecycle, and credentials.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.academics.schemas import (
    StudentCreateRequest,
    StudentCredentialSlipResponse,
    SectionRosterResponse,
    RosterStatusUpdateRequest,
    RosterChangeCreateRequest,
    RosterChangeReviewRequest,
    RosterChangeResponse,
)
from backend.app.academics import roster_service

router = APIRouter(prefix="/rosters", tags=["Rosters & Students"])


@router.get("/{section_id}", response_model=SectionRosterResponse)
async def get_section_roster_endpoint(
    section_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetches full section roster, enrolled students, designated Class Teacher, and status."""
    return await roster_service.get_section_roster(db, current_user, section_id)


@router.post("/{section_id}/students", response_model=StudentCredentialSlipResponse, status_code=status.HTTP_201_CREATED)
async def add_student_endpoint(
    section_id: str,
    payload: StudentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Class Teacher or Coordinator adds a single student with roll number to section."""
    return await roster_service.add_student_to_section(db, current_user, section_id, payload)


@router.post("/{section_id}/students/bulk")
async def bulk_add_students_endpoint(
    section_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Class Teacher or Coordinator bulk imports students via CSV."""
    content = await file.read()
    csv_text = content.decode("utf-8")
    return await roster_service.bulk_add_students_csv(db, current_user, section_id, csv_text)


@router.patch("/{section_id}/status")
async def update_roster_status_endpoint(
    section_id: str,
    payload: RosterStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Class Teacher or Coordinator updates roster status (pending -> verified -> locked)."""
    return await roster_service.update_roster_status(db, current_user, section_id, payload.status)


@router.post("/{section_id}/change-requests", response_model=RosterChangeResponse, status_code=status.HTTP_201_CREATED)
async def request_roster_change_endpoint(
    section_id: str,
    payload: RosterChangeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Class Teacher requests modifications on a locked roster."""
    return await roster_service.request_roster_change(db, current_user, section_id, payload)


@router.get("/{section_id}/change-requests", response_model=List[RosterChangeResponse])
async def list_roster_changes_endpoint(
    section_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists roster change requests for the given section."""
    return await roster_service.list_roster_changes(db, current_user, section_id)


@router.patch("/change-requests/{request_id}/review", response_model=RosterChangeResponse)
async def review_roster_change_endpoint(
    request_id: str,
    payload: RosterChangeReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Academic Coordinator or Admin approves or rejects a roster change request."""
    return await roster_service.review_roster_change(db, current_user, request_id, payload)


@router.get("/{section_id}/credentials", response_model=List[StudentCredentialSlipResponse])
async def get_credential_slips_endpoint(
    section_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates printable credential distribution slips for all students in section."""
    return await roster_service.get_credential_slips(db, current_user, section_id)

