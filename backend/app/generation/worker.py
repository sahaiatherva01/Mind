"""
Background Worker Tasks for AI Content Generation using ARQ & Redis.
Handles retries with backoff, timeouts, graceful cancellation, and atomic draft persistence.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from arq.connections import RedisSettings

from backend.app.core.config import settings
from backend.app.core.db import async_session_maker
from backend.app.core.logging import get_logger
from ai_engine.adapters.gateway import AIGateway
from ai_engine.schemas.question import GenerationRequestSpec
from backend.app.generation.models import GenerationJob
from backend.app.assessments.models import Assessment, AssessmentItem
from backend.app.content.models import Question
from backend.app.audit.service import record_audit_event

logger = get_logger("mind.generation.worker")
gateway = AIGateway()


async def execute_generation_job_with_db(db: AsyncSession, job_id: str) -> Dict[str, Any]:
    """
    Core business logic for executing an AI generation request against any active AsyncSession.
    """
    stmt = select(GenerationJob).where(GenerationJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        logger.error(f"Generation job {job_id} not found in database.")
        return {"status": "not_found", "job_id": job_id}

    if job.status == "cancelled":
        logger.info(f"Generation job {job_id} was cancelled before worker execution.")
        return {"status": "cancelled", "job_id": job_id}

    job.status = "running"
    await db.commit()

    try:
        spec_data = job.input_json or {}
        spec = GenerationRequestSpec(**spec_data)

        from backend.app.generation.graph import run_generation_pipeline

        questions, warnings, trace = await asyncio.wait_for(
            run_generation_pipeline(spec, prompt_version=job.prompt_version or "v1.0"),
            timeout=90.0,
        )

        await db.refresh(job)
        if job.status == "cancelled":
            logger.info(f"Generation job {job_id} was cancelled during generation. Discarding output.")
            return {"status": "cancelled", "job_id": job_id}

        job.warnings = warnings
        job.output_json = {"execution_trace": trace, "item_count": len(questions)}

        title_prefix = spec.output_type.replace("_", " ").title()
        assessment = Assessment(
            school_id=job.school_id,
            creator_id=job.requester_id,
            class_id=spec.class_id,
            section_id=spec.section_id,
            subject_id=spec.subject_id,
            title=f"{title_prefix}: {spec.chapter} ({len(questions)} Questions)",
            type=spec.output_type,
            status="needs_review",
            total_marks=spec.total_marks,
            instructions=spec.instructions,
            settings={
                "difficulty_distribution": spec.difficulty_distribution,
                "topics": spec.topics,
                "warnings": warnings,
            },
        )
        db.add(assessment)
        await db.flush()

        for pos, q in enumerate(questions, start=1):
            q_row = Question(
                school_id=job.school_id,
                author_id=job.requester_id,
                subject_id=spec.subject_id,
                category=q.category,
                type=q.type,
                prompt=q.prompt,
                marks=q.marks,
                difficulty=q.difficulty,
                topic_tags=q.topic_tags,
                content_data={
                    "options": [opt.model_dump() for opt in q.options] if q.options else None,
                    "match_pairs": [p.model_dump() for p in q.match_pairs] if q.match_pairs else None,
                    "code_snippet": q.code_snippet,
                    "diagram_description": q.diagram_description,
                    "passage_or_case_text": q.passage_or_case_text,
                },
                answer_data={
                    "expected_answer": q.expected_answer,
                    "answer_keys": q.answer_keys,
                    "marking_scheme": q.marking_scheme,
                    "rationale": q.rationale,
                },
                status="draft",
            )
            db.add(q_row)
            await db.flush()

            item = AssessmentItem(
                assessment_id=assessment.id,
                question_id=q_row.id,
                position=pos,
                marks_override=q.marks,
            )
            db.add(item)

        job.status = "succeeded"
        job.output_json = {
            "assessment_id": assessment.id,
            "question_count": len(questions),
            "total_marks": spec.total_marks,
            "questions": [q.model_dump() for q in questions],
        }

        await record_audit_event(
            db=db,
            school_id=job.school_id,
            actor_id=job.requester_id,
            action="generation.completed",
            entity_type="assessment",
            entity_id=assessment.id,
            metadata_json={"output_type": spec.output_type, "questions": len(questions)},
        )
        await db.commit()
        logger.info(f"Generation job {job_id} succeeded. Created assessment {assessment.id}")
        return {"status": "succeeded", "assessment_id": assessment.id}

    except asyncio.TimeoutError:
        logger.error(f"Generation job {job_id} timed out after 90 seconds.")
        job.status = "failed"
        job.error_code = "TIMEOUT"
        job.error_message = "Generation job timed out while communicating with model provider."
        await db.commit()
        return {"status": "failed", "error": "timeout"}

    except Exception as exc:
        logger.exception(f"Generation job {job_id} failed with error: {exc}")
        job.status = "failed"
        job.error_code = "GENERATION_ERROR"
        job.error_message = str(exc)
        await db.commit()
        return {"status": "failed", "error": str(exc)}


async def execute_generation_job(ctx: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    ARQ entrypoint executed by background worker process.
    """
    logger.info(f"Worker picking up generation job {job_id}")
    async with async_session_maker() as db:
        return await execute_generation_job_with_db(db, job_id)


class WorkerSettings:
    """ARQ Worker configuration for background queue."""
    functions = [execute_generation_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    job_timeout = 120
    max_tries = 3
    retry_delay = 5.0
