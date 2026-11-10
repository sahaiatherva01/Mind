"""
Content & Materials API Routers: Teacher Material Distribution, Question Extraction & Student My Learning
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.content import service
from backend.app.content.schemas import (
    MaterialCreate,
    MaterialOut,
    StudentMaterialOut,
    MaterialOpenPayload,
    QuestionExtractionRequest,
    QuestionApprovalRequest,
)

content_router = APIRouter(prefix="/content", tags=["Learning Materials & Content"])
student_learning_router = APIRouter(prefix="/student", tags=["Student Learning"])


# --- Teacher / Staff Content Endpoints ---

@content_router.get("/materials", response_model=List[MaterialOut])
async def list_materials(
    class_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists learning materials created or visible to teacher/coordinator/admin."""
    return await service.list_materials_for_actor(
        db=db, actor=current_user, class_id=class_id, subject_id=subject_id
    )


@content_router.post("/materials", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
async def create_material(
    payload: MaterialCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Uploads and distributes learning material to specified sections with assignment validation."""
    mat = await service.create_and_distribute_material(
        db=db, actor=current_user, data=payload
    )
    return await service.get_material_detail(db=db, actor=current_user, material_id=mat.id)


@content_router.get("/materials/{material_id}", response_model=MaterialOut)
async def get_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Gets details and engagement metrics for a single material."""
    return await service.get_material_detail(
        db=db, actor=current_user, material_id=material_id
    )


@content_router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft deletes / archives learning material."""
    await service.delete_material(
        db=db, actor=current_user, material_id=material_id
    )
    return None


@content_router.post("/materials/{material_id}/extract-questions")
async def extract_questions(
    material_id: str,
    payload: QuestionExtractionRequest = QuestionExtractionRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Runs Question Extractor Agent on material text. Outputs draft items in needs_review state."""
    job = await service.trigger_question_extraction(
        db=db, actor=current_user, material_id=material_id, max_questions=payload.max_questions
    )
    return {
        "job_id": job.id,
        "material_id": job.material_id,
        "status": job.status,
        "extracted_count": job.extracted_count,
        "questions": job.results_json,
    }


@content_router.post("/materials/{material_id}/approve-question", status_code=status.HTTP_201_CREATED)
async def approve_question(
    material_id: str,
    payload: QuestionApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approves an extracted candidate question into the canonical school Question Bank."""
    q = await service.approve_extracted_question(
        db=db, actor=current_user, material_id=material_id, payload=payload
    )
    return {
        "status": "approved",
        "question_id": q.id,
        "prompt": q.prompt,
        "category": q.category,
        "type": q.type,
        "marks": q.marks,
    }


# --- Student My Learning Endpoints ---

@student_learning_router.get("/my-learning", response_model=List[StudentMaterialOut])
async def get_my_learning_materials(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists learning materials distributed to the active enrolled section(s) of the student."""
    return await service.list_materials_for_student(
        db=db, student=current_user
    )


@student_learning_router.post("/my-learning/{material_id}/open")
async def open_learning_material(
    material_id: str,
    payload: MaterialOpenPayload = MaterialOpenPayload(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tracks material reading / open events with engagement telemetry."""
    engagement = await service.record_student_open_event(
        db=db,
        student=current_user,
        material_id=material_id,
        duration_seconds=payload.duration_seconds,
        pages_read=payload.pages_read,
    )
    return {
        "status": "tracked",
        "material_id": engagement.material_id,
        "opened_at": engagement.opened_at,
        "duration_seconds": engagement.duration_seconds,
    }
