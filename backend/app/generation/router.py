"""
Generation Router: Worksheets, Quizzes, Question Papers, Custom Question Sets
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user
from backend.app.identity.models import User
from backend.app.generation import service, policies
from backend.app.generation.schemas import (
    WorksheetGenerateRequest,
    QuizGenerateRequest,
    QuestionPaperGenerateRequest,
    CustomQuestionGenerateRequest,
    JobResponse,
    JobDetailResponse,
)
from ai_engine.schemas.question import GenerationRequestSpec

router = APIRouter(prefix="/generation", tags=["AI Generation"])


@router.post("/worksheets", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_worksheet(
    payload: WorksheetGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await policies.can_generate_for_workspace(
        db, current_user, payload.class_id, payload.section_id, payload.subject_id
    )
    spec = GenerationRequestSpec(
        output_type="worksheet",
        subject_id=payload.subject_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        chapter=payload.chapter,
        topics=payload.topics,
        question_types=payload.question_types,
        question_count=payload.question_count,
        total_marks=payload.total_marks,
        difficulty_distribution=payload.difficulty,
        instructions=payload.instructions,
        board=payload.board,
        language=payload.language,
    )
    job, _ = await service.queue_and_execute_generation(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        spec=spec,
    )
    return JobResponse(job_id=job.id, status=job.status, created_at=job.created_at)


@router.post("/quizzes", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_quiz(
    payload: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await policies.can_generate_for_workspace(
        db, current_user, payload.class_id, payload.section_id, payload.subject_id
    )
    spec = GenerationRequestSpec(
        output_type="quiz",
        subject_id=payload.subject_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        chapter=payload.chapter,
        topics=payload.topics,
        question_types=payload.question_types,
        question_count=payload.question_count,
        total_marks=payload.total_marks,
        difficulty_distribution=payload.difficulty,
        instructions=payload.instructions,
        board=payload.board,
        language=payload.language,
    )
    job, _ = await service.queue_and_execute_generation(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        spec=spec,
    )
    return JobResponse(job_id=job.id, status=job.status, created_at=job.created_at)


@router.post("/question-papers", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_question_paper(
    payload: QuestionPaperGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await policies.can_generate_for_workspace(
        db, current_user, payload.class_id, payload.section_id, payload.subject_id
    )
    spec = GenerationRequestSpec(
        output_type="question_paper",
        subject_id=payload.subject_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        chapter=payload.chapter,
        topics=payload.topics,
        question_types=payload.question_types,
        question_count=payload.question_count,
        total_marks=payload.total_marks,
        difficulty_distribution=payload.difficulty,
        instructions=payload.instructions,
        board=payload.board,
        language=payload.language,
    )
    job, _ = await service.queue_and_execute_generation(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        spec=spec,
    )
    return JobResponse(job_id=job.id, status=job.status, created_at=job.created_at)


@router.post("/questions", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_custom_questions(
    payload: CustomQuestionGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await policies.can_generate_for_workspace(
        db, current_user, payload.class_id, payload.section_id, payload.subject_id
    )
    spec = GenerationRequestSpec(
        output_type="custom_question_set",
        subject_id=payload.subject_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        chapter=payload.chapter,
        topics=payload.topics,
        question_types=payload.question_types,
        question_count=payload.question_count,
        total_marks=payload.total_marks,
        difficulty_distribution=payload.difficulty,
        instructions=payload.instructions,
        board=payload.board,
        language=payload.language,
    )
    job, _ = await service.queue_and_execute_generation(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        spec=spec,
    )
    return JobResponse(job_id=job.id, status=job.status, created_at=job.created_at)


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job_status_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await service.get_generation_job(db, current_user.school_id, job_id)
    out_json = job.output_json or {}
    return JobDetailResponse(
        id=job.id,
        status=job.status,
        model=job.model,
        warnings=job.warnings or [],
        error_code=job.error_code,
        error_message=job.error_message,
        assessment_id=out_json.get("assessment_id"),
        questions=out_json.get("questions"),
        created_at=job.created_at,
    )


@router.post("/jobs/{job_id}/cancel", response_model=JobDetailResponse)
async def cancel_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await service.cancel_generation_job(db, current_user.school_id, job_id)
    return JobDetailResponse(
        id=job.id,
        status=job.status,
        model=job.model,
        warnings=job.warnings or [],
        error_code=job.error_code,
        error_message=job.error_message,
        created_at=job.created_at,
    )

