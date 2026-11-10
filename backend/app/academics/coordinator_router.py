"""
Academic Coordinator Router — Mind V2
Base Path: /api/v1/coordinator
Endpoints strictly scoped to the Coordinator's assigned grade band.
"""
from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.identity.models import User, RoleName
from backend.app.academics.schemas import (
    BandSummaryResponse,
    AssignmentMatrixItem,
    CoordinatorTeacherCreateRequest,
    TeacherAssignmentCreateRequest,
    TeacherAssignmentResponse,
    CurriculumNodeResponse,
)
from backend.app.academics import coordinator_service

router = APIRouter(prefix="/coordinator", tags=["Academic Coordinator"])


class TeacherStatusToggleRequest(BaseModel):
    active: bool


@router.get("/band-summary", response_model=BandSummaryResponse)
async def get_band_summary_endpoint(
    current_user: User = Depends(require_role([RoleName.ACADEMIC_COORDINATOR, RoleName.SCHOOL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Fetches high-level summary metrics and class structure for the coordinator's band."""
    return await coordinator_service.get_band_summary(db, current_user)


@router.get("/teachers", response_model=List[Dict[str, Any]])
async def list_band_teachers_endpoint(
    current_user: User = Depends(require_role([RoleName.ACADEMIC_COORDINATOR, RoleName.SCHOOL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Lists all teachers who have assignments within the coordinator's band."""
    return await coordinator_service.list_band_teachers(db, current_user)


@router.post("/teachers", status_code=status.HTTP_201_CREATED)
async def create_band_teacher_endpoint(
    payload: CoordinatorTeacherCreateRequest,
    current_user: User = Depends(require_role([RoleName.ACADEMIC_COORDINATOR, RoleName.SCHOOL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Provisions a new teacher and assigns them to a class in the coordinator's band."""
    return await coordinator_service.create_band_teacher(db, current_user, payload)


@router.patch("/teachers/{teacher_id}/status")
async def toggle_band_teacher_status_endpoint(
    teacher_id: str,
    payload: TeacherStatusToggleRequest,
    current_user: User = Depends(require_role([RoleName.ACADEMIC_COORDINATOR, RoleName.SCHOOL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Enables or disables a teacher who teaches in the coordinator's band."""
    return await coordinator_service.toggle_band_teacher_status(db, current_user, teacher_id, payload.active)


@router.get("/assignments", response_model=List[AssignmentMatrixItem])
async def get_assignment_matrix_endpoint(
    current_user: User = Depends(require_role([RoleName.ACADEMIC_COORDINATOR, RoleName.SCHOOL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Returns the Teacher x Class x Section x Subject assignment matrix for this band."""
    return await coordinator_service.get_assignment_matrix(db, current_user)


@router.post("/assignments", response_model=TeacherAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_teacher_in_band_endpoint(
    payload: TeacherAssignmentCreateRequest,
    current_user: User = Depends(require_role([RoleName.ACADEMIC_COORDINATOR, RoleName.SCHOOL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Assigns a teacher to a section and subject within the coordinator's band."""
    raw = await coordinator_service.assign_teacher_in_band(db, current_user, payload)
    return TeacherAssignmentResponse.model_validate(raw)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_band_assignment_endpoint(
    assignment_id: str,
    current_user: User = Depends(require_role([RoleName.ACADEMIC_COORDINATOR, RoleName.SCHOOL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Removes a teacher assignment from the coordinator's band."""
    await coordinator_service.delete_band_assignment(db, current_user, assignment_id)
    return None


@router.get("/curriculum", response_model=List[CurriculumNodeResponse])
async def list_band_curriculum_endpoint(
    current_user: User = Depends(require_role([RoleName.ACADEMIC_COORDINATOR, RoleName.SCHOOL_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Fetches curriculum chapters and learning outcomes for grades in the coordinator's band."""
    return await coordinator_service.list_band_curriculum(db, current_user)
