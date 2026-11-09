"""
Generation Service: Orchestrates async job queueing, worker dispatch, cancellation, and retrieval.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis

from ai_engine.schemas.question import GenerationRequestSpec
from backend.app.core.config import settings
from backend.app.core.errors import NotFoundException, ValidationException
from backend.app.core.logging import get_logger
from backend.app.generation.models import GenerationJob
from backend.app.generation.worker import execute_generation_job

logger = get_logger("mind.generation.service")
_redis_pool: Optional[ArqRedis] = None


async def get_arq_pool() -> Optional[ArqRedis]:
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = await asyncio.wait_for(
                create_pool(RedisSettings.from_dsn(settings.REDIS_URL)),
                timeout=1.0,
            )
        except Exception as e:
            logger.debug(f"Redis not available for arq queue ({e}). Running with fallback task runner.")
            _redis_pool = None
    return _redis_pool


async def queue_and_execute_generation(
    db: AsyncSession,
    school_id: str,
    user_id: str,
    spec: GenerationRequestSpec,
    idempotency_key: Optional[str] = None,
) -> Tuple[GenerationJob, Optional[Any]]:
    """
    Persists the generation job in 'queued' state and delegates execution to background worker.
    Returns HTTP 202 immediately to free up the web server.
    """
    # 1. Create generation job in 'queued' state
    job = GenerationJob(
        school_id=school_id,
        requester_id=user_id,
        status="queued",
        model=settings.AI_PROVIDER,
        prompt_version="v1.0",
        input_json=spec.model_dump(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # In test environments (isolated in-memory SQLite fixtures), run directly with test session
    if settings.ENVIRONMENT == "test":
        from backend.app.generation.worker import execute_generation_job_with_db
        await execute_generation_job_with_db(db, job.id)
        await db.refresh(job)
        return job, None

    # 2. Dispatch to ARQ Redis worker for production/dev
    pool = await get_arq_pool()
    if pool is not None:
        try:
            await pool.enqueue_job("execute_generation_job", job.id)
            logger.info(f"Enqueued job {job.id} to Arq Redis queue.")
            return job, None
        except Exception as err:
            logger.warning(f"Failed to enqueue to Redis ({err}). Executing via background task.")

    # 3. Fallback when Redis is offline in local dev
    asyncio.create_task(execute_generation_job({}, job.id))
    return job, None


async def get_generation_job(db: AsyncSession, school_id: str, job_id: str) -> GenerationJob:
    stmt = select(GenerationJob).where(GenerationJob.id == job_id, GenerationJob.school_id == school_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException("GenerationJob", job_id)
    return job


async def cancel_generation_job(db: AsyncSession, school_id: str, job_id: str) -> GenerationJob:
    job = await get_generation_job(db, school_id, job_id)
    if job.status in ["succeeded", "failed"]:
        raise ValidationException(f"Cannot cancel a job that has already {job.status}.")

    job.status = "cancelled"
    job.error_code = "USER_CANCELLED"
    job.error_message = "Generation job was cancelled by the teacher."
    await db.commit()
    await db.refresh(job)
    logger.info(f"Job {job_id} marked as cancelled.")
    return job
