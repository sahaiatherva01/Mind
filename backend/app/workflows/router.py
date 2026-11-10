"""
Advanced Academic Workflows Router — Mind V2 (Phase 8)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.workflows.schemas import (
    EarlyWarningSignal,
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
    SmartGroupCreate,
    SmartGroupResponse,
    RemedialGenerationResponse,
    SubstituteTeacherAssignRequest,
    SubstituteTeacherResponse,
    StudentGoalCreate,
    StudentGoalResponse,
    StudentDoubtCreate,
    DoubtAnswerRequest,
    StudentDoubtResponse,
    RevisionItem,
)
from backend.app.workflows.service import WorkflowService

router = APIRouter(tags=["Advanced Academic Workflows"])


# --- Early Warnings & Coordinator Interventions ---

@router.get("/coordinator/early-warnings", response_model=List[EarlyWarningSignal])
async def get_early_warning_signals(
    band_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve at-risk student warning signals across band (declining trends, low averages, zero reading)."""
    return await WorkflowService.get_early_warning_signals(db, current_user, band_id)


@router.post("/coordinator/interventions", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
async def create_intervention(
    payload: InterventionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log an academic coordinator intervention for an at-risk student."""
    return await WorkflowService.create_intervention(db, current_user, payload)


@router.patch("/coordinator/interventions/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: str,
    payload: InterventionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update intervention status (in_progress, resolved), action taken, and notes."""
    return await WorkflowService.update_intervention(db, current_user, intervention_id, payload)


@router.get("/coordinator/interventions", response_model=List[InterventionResponse])
async def list_interventions(
    band_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tracked coordinator interventions."""
    return await WorkflowService.list_interventions(db, current_user, band_id)


# --- Smart Student Groups & Remedial Generation ---

@router.post("/teacher/smart-groups", response_model=SmartGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_smart_group(
    payload: SmartGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a dynamically segmented student cohort (remedial, core, advanced)."""
    return await WorkflowService.create_smart_group(db, current_user, payload)


@router.get("/teacher/smart-groups", response_model=List[SmartGroupResponse])
async def list_smart_groups(
    section_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List smart student groups within teacher's scope."""
    return await WorkflowService.list_smart_groups(db, current_user, section_id, subject_id)


@router.post("/teacher/smart-groups/{group_id}/generate-remedial", response_model=RemedialGenerationResponse)
async def generate_remedial_worksheet(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """One-click generation of targeted practice worksheet addressing smart group's weakest topics."""
    return await WorkflowService.generate_remedial_worksheet(db, current_user, group_id)


# --- Substitution Manager ---

@router.post("/coordinator/substitutions", response_model=SubstituteTeacherResponse, status_code=status.HTTP_201_CREATED)
async def assign_substitute_teacher(
    payload: SubstituteTeacherAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign substitute teacher with automated temporal access revocation."""
    return await WorkflowService.assign_substitute_teacher(db, current_user, payload)


# --- Student Academic Goals & Doubts ---

@router.post("/student/goals", response_model=StudentGoalResponse, status_code=status.HTTP_201_CREATED)
async def set_student_goal(
    payload: StudentGoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set personal target score and completion date for a subject."""
    return await WorkflowService.create_or_update_student_goal(db, current_user, payload)


@router.get("/student/goals", response_model=List[StudentGoalResponse])
async def get_student_goals(
    student_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve tracked student academic goals."""
    return await WorkflowService.get_student_goals(db, current_user, student_id)


@router.get("/student/revision-list", response_model=List[RevisionItem])
async def get_student_revision_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve personalized revision list of previously missed questions."""
    return await WorkflowService.get_student_revision_list(db, current_user)


@router.post("/student/doubts", response_model=StudentDoubtResponse, status_code=status.HTTP_201_CREATED)
async def submit_student_doubt(
    payload: StudentDoubtCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit structured academic query/doubt to assigned subject teacher."""
    return await WorkflowService.submit_student_doubt(db, current_user, payload)


@router.patch("/teacher/doubts/{doubt_id}/answer", response_model=StudentDoubtResponse)
async def answer_student_doubt(
    doubt_id: str,
    payload: DoubtAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Teacher answers student doubt query."""
    return await WorkflowService.answer_student_doubt(db, current_user, doubt_id, payload)


@router.get("/student/doubts", response_model=List[StudentDoubtResponse])
async def list_student_doubts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List doubt queries relevant to student or teacher."""
    return await WorkflowService.list_student_doubts(db, current_user)

