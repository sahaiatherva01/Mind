"""
Assessments Router: Draft Review, Editing, Item Operations, and Approval
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.assessments import service, policies
from backend.app.assessments.schemas import (
    AssessmentResponse,
    AssessmentUpdateRequest,
    AssessmentItemUpdateRequest,
    ItemRegenerateRequest,
)

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("", response_model=List[AssessmentResponse])
async def list_assessments_endpoint(
    class_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    creator_id = current_user.id if current_user.role == "teacher" else None
    assessments = await service.list_assessments(
        db,
        school_id=current_user.school_id,
        creator_id=creator_id,
        class_id=class_id,
        subject_id=subject_id,
        status=status,
    )
    return [AssessmentResponse.model_validate(a) for a in assessments]


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment_endpoint(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment = await service.get_assessment_by_id(db, current_user.school_id, assessment_id)
    policies.can_view_assessment_draft(current_user, assessment)
    return AssessmentResponse.model_validate(assessment)


@router.patch("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment_endpoint(
    assessment_id: str,
    payload: AssessmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment = await service.get_assessment_by_id(db, current_user.school_id, assessment_id)
    policies.can_manage_assessment(current_user, assessment)
    updated = await service.update_assessment(db, current_user.school_id, assessment_id, payload)
    return AssessmentResponse.model_validate(updated)


@router.patch("/{assessment_id}/items/{item_id}", response_model=AssessmentResponse)
async def update_item_endpoint(
    assessment_id: str,
    item_id: str,
    payload: AssessmentItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment = await service.get_assessment_by_id(db, current_user.school_id, assessment_id)
    policies.can_manage_assessment(current_user, assessment)
    updated = await service.update_assessment_item(db, current_user.school_id, assessment_id, item_id, payload)
    return AssessmentResponse.model_validate(updated)


@router.delete("/{assessment_id}/items/{item_id}", response_model=AssessmentResponse)
async def delete_item_endpoint(
    assessment_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment = await service.get_assessment_by_id(db, current_user.school_id, assessment_id)
    policies.can_manage_assessment(current_user, assessment)
    updated = await service.delete_assessment_item(db, current_user.school_id, assessment_id, item_id)
    return AssessmentResponse.model_validate(updated)


@router.post("/{assessment_id}/items/{item_id}/regenerate", response_model=AssessmentResponse)
async def regenerate_item_endpoint(
    assessment_id: str,
    item_id: str,
    payload: ItemRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment = await service.get_assessment_by_id(db, current_user.school_id, assessment_id)
    policies.can_manage_assessment(current_user, assessment)
    updated = await service.regenerate_assessment_item(
        db, current_user.school_id, assessment_id, item_id, payload.feedback
    )
    return AssessmentResponse.model_validate(updated)


@router.post("/{assessment_id}/reorder", response_model=AssessmentResponse)
async def reorder_items_endpoint(
    assessment_id: str,
    item_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment = await service.get_assessment_by_id(db, current_user.school_id, assessment_id)
    policies.can_manage_assessment(current_user, assessment)
    updated = await service.reorder_assessment_items(db, current_user.school_id, assessment_id, item_ids)
    return AssessmentResponse.model_validate(updated)


@router.post("/{assessment_id}/approve", response_model=AssessmentResponse)
async def approve_assessment_endpoint(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assessment = await service.get_assessment_by_id(db, current_user.school_id, assessment_id)
    policies.can_manage_assessment(current_user, assessment)
    approved = await service.approve_assessment(db, current_user.school_id, assessment_id, current_user.id)
    return AssessmentResponse.model_validate(approved)


from backend.app.assessments.export_service import AssessmentExportService


@router.get("/{assessment_id}/export/csv")
async def export_assessment_csv_endpoint(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export student gradebook roster and score breakdown as CSV."""
    return await AssessmentExportService.export_results_csv(db, current_user, assessment_id)


@router.get("/{assessment_id}/export/pdf")
async def export_assessment_printable_endpoint(
    assessment_id: str,
    include_marking_scheme: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export clean Board-exam printable paper with optional teacher marking scheme."""
    return await AssessmentExportService.export_printable_paper(
        db, current_user, assessment_id, include_marking_scheme
    )

