"""
Generation Service
Orchestrates AI Gateway calls, domain validation, assessment draft generation, and job state transitions.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_engine.adapters.gateway import AIGateway
from ai_engine.schemas.question import GenerationRequestSpec, CanonicalQuestion
from backend.app.core.errors import NotFoundException, ValidationException
from backend.app.generation.models import GenerationJob
from backend.app.assessments.models import Assessment, AssessmentItem
from backend.app.content.models import Question
from backend.app.audit.service import record_audit_event


gateway = AIGateway()


async def queue_and_execute_generation(
    db: AsyncSession,
    school_id: str,
    user_id: str,
    spec: GenerationRequestSpec,
) -> Tuple[GenerationJob, Optional[Assessment]]:
    # 1. Create generation job in queued state
    job = GenerationJob(
        school_id=school_id,
        requester_id=user_id,
        status="running",
        model=gateway.provider_name,
        prompt_version="v1.0",
        input_json=spec.model_dump(),
    )
    db.add(job)
    await db.flush()

    try:
        # 2. Call AI Gateway
        questions, warnings = await gateway.generate_draft(spec, prompt_version="v1.0")
        job.warnings = warnings

        # 3. Create Assessment Draft (needs_review)
        title_prefix = spec.output_type.replace("_", " ").title()
        assessment = Assessment(
            school_id=school_id,
            creator_id=user_id,
            class_id=spec.class_id,
            section_id=spec.section_id,
            subject_id=spec.subject_id,
            title=f"{title_prefix}: {spec.chapter} ({len(questions)} Questions)",
            type=spec.output_type,
            status="needs_review",  # Human-in-the-loop: Teacher review required
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

        # 4. Save Questions and link as AssessmentItems
        for pos, q in enumerate(questions, start=1):
            q_row = Question(
                school_id=school_id,
                author_id=user_id,
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
            school_id=school_id,
            actor_id=user_id,
            action="generation.completed",
            entity_type="assessment",
            entity_id=assessment.id,
            metadata_json={"output_type": spec.output_type, "questions": len(questions)},
        )

        return job, assessment

    except Exception as ex:
        job.status = "failed"
        job.error_code = "GENERATION_ERROR"
        job.error_message = str(ex)
        await db.flush()
        raise ex


async def get_generation_job(db: AsyncSession, school_id: str, job_id: str) -> GenerationJob:
    stmt = select(GenerationJob).where(GenerationJob.id == job_id, GenerationJob.school_id == school_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise NotFoundException("GenerationJob", job_id)
    return job


async def cancel_generation_job(db: AsyncSession, school_id: str, job_id: str) -> GenerationJob:
    job = await get_generation_job(db, school_id, job_id)
    if job.status in ("succeeded", "failed"):
        raise ValidationException(f"Cannot cancel job with terminal status '{job.status}'")

    job.status = "cancelled"
    await db.flush()
    return job

