"""
Assessment Service
Handles draft editing, item reordering, item regeneration, and mandatory teacher approval.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import NotFoundException, ValidationException, ConflictException
from backend.app.assessments.models import Assessment, AssessmentItem
from backend.app.content.models import Question
from backend.app.assessments.schemas import AssessmentUpdateRequest, AssessmentItemUpdateRequest
from ai_engine.adapters.gateway import AIGateway
from ai_engine.schemas.question import CanonicalQuestion
from backend.app.audit.service import record_audit_event

gateway = AIGateway()


async def list_assessments(
    db: AsyncSession,
    school_id: str,
    creator_id: Optional[str] = None,
    class_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Assessment]:
    stmt = (
        select(Assessment)
        .options(
            selectinload(Assessment.items).selectinload(AssessmentItem.question)
        )
        .where(Assessment.school_id == school_id)
    )
    if creator_id:
        stmt = stmt.where(Assessment.creator_id == creator_id)
    if class_id:
        stmt = stmt.where(Assessment.class_id == class_id)
    if subject_id:
        stmt = stmt.where(Assessment.subject_id == subject_id)
    if status:
        stmt = stmt.where(Assessment.status == status)

    stmt = stmt.order_by(Assessment.updated_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_assessment_by_id(db: AsyncSession, school_id: str, assessment_id: str) -> Assessment:
    stmt = (
        select(Assessment)
        .options(
            selectinload(Assessment.items).selectinload(AssessmentItem.question)
        )
        .where(Assessment.id == assessment_id, Assessment.school_id == school_id)
    )
    res = await db.execute(stmt)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise NotFoundException("Assessment", assessment_id)
    return assessment


async def update_assessment(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    data: AssessmentUpdateRequest,
) -> Assessment:
    assessment = await get_assessment_by_id(db, school_id, assessment_id)
    if assessment.status in ("published", "closed"):
        raise ValidationException("Published assessment versions are immutable.")

    if data.title is not None:
        assessment.title = data.title.strip()
    if data.instructions is not None:
        assessment.instructions = data.instructions.strip()

    await db.flush()
    return assessment


async def update_assessment_item(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    item_id: str,
    data: AssessmentItemUpdateRequest,
) -> Assessment:
    assessment = await get_assessment_by_id(db, school_id, assessment_id)
    if assessment.status in ("published", "closed"):
        raise ValidationException("Published assessment versions are immutable.")

    item_stmt = select(AssessmentItem).where(
        AssessmentItem.id == item_id, AssessmentItem.assessment_id == assessment_id
    )
    res_item = await db.execute(item_stmt)
    item = res_item.scalar_one_or_none()
    if not item:
        raise NotFoundException("AssessmentItem", item_id)

    q_stmt = select(Question).where(Question.id == item.question_id)
    res_q = await db.execute(q_stmt)
    question = res_q.scalar_one()

    if data.prompt is not None:
        question.prompt = data.prompt.strip()
    if data.marks is not None:
        item.marks_override = data.marks
        question.marks = data.marks
    if data.expected_answer is not None:
        ans_data = dict(question.answer_data)
        ans_data["expected_answer"] = data.expected_answer
        question.answer_data = ans_data
    if data.options is not None:
        c_data = dict(question.content_data)
        c_data["options"] = data.options
        question.content_data = c_data

    question.version += 1
    # Recalculate total marks
    assessment.total_marks = sum(
        (i.marks_override if i.marks_override is not None else i.question.marks)
        for i in assessment.items
    )

    await db.flush()
    return await get_assessment_by_id(db, school_id, assessment_id)


async def delete_assessment_item(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    item_id: str,
) -> Assessment:
    assessment = await get_assessment_by_id(db, school_id, assessment_id)
    if assessment.status in ("published", "closed"):
        raise ValidationException("Published assessment versions are immutable.")

    target_item = None
    for item in assessment.items:
        if item.id == item_id:
            target_item = item
            break

    if not target_item:
        raise NotFoundException("AssessmentItem", item_id)

    await db.delete(target_item)
    await db.flush()

    # Reorder remaining items
    remaining = [i for i in assessment.items if i.id != item_id]
    for idx, rem in enumerate(remaining, start=1):
        rem.position = idx

    assessment.total_marks = sum(
        (i.marks_override if i.marks_override is not None else i.question.marks)
        for i in remaining
    )

    await db.flush()
    return await get_assessment_by_id(db, school_id, assessment_id)


async def reorder_assessment_items(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    item_ids_in_order: List[str],
) -> Assessment:
    assessment = await get_assessment_by_id(db, school_id, assessment_id)
    if assessment.status in ("published", "closed"):
        raise ValidationException("Published assessment versions are immutable.")

    item_map = {item.id: item for item in assessment.items}
    for new_pos, i_id in enumerate(item_ids_in_order, start=1):
        if i_id in item_map:
            item_map[i_id].position = new_pos

    await db.flush()
    return await get_assessment_by_id(db, school_id, assessment_id)


async def regenerate_assessment_item(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    item_id: str,
    feedback: str,
) -> Assessment:
    """Regenerates a single item without discarding any other teacher edits."""
    assessment = await get_assessment_by_id(db, school_id, assessment_id)
    if assessment.status in ("published", "closed"):
        raise ValidationException("Published assessment versions are immutable.")

    target_item = next((i for i in assessment.items if i.id == item_id), None)
    if not target_item:
        raise NotFoundException("AssessmentItem", item_id)

    old_q = target_item.question

    canonical_q = CanonicalQuestion(
        id=old_q.id,
        category=old_q.category,  # type: ignore
        type=old_q.type,  # type: ignore
        prompt=old_q.prompt,
        marks=old_q.marks,
        difficulty=old_q.difficulty,  # type: ignore
        topic_tags=old_q.topic_tags or [],
        options=old_q.content_data.get("options") if old_q.content_data else None,
        expected_answer=old_q.answer_data.get("expected_answer", "") if old_q.answer_data else "",
        version=old_q.version,
    )

    regenerated = await gateway.regenerate_item(canonical_q, feedback)

    old_q.prompt = regenerated.prompt
    old_q.version += 1
    if regenerated.options:
        c_data = dict(old_q.content_data or {})
        c_data["options"] = [opt.model_dump() for opt in regenerated.options]
        old_q.content_data = c_data
    if regenerated.expected_answer:
        a_data = dict(old_q.answer_data or {})
        a_data["expected_answer"] = regenerated.expected_answer
        old_q.answer_data = a_data

    await db.flush()
    return await get_assessment_by_id(db, school_id, assessment_id)


async def approve_assessment(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    actor_id: str,
) -> Assessment:
    """
    Mandatory Teacher Sign-off Gate.
    Transitions status to 'approved'.
    """
    assessment = await get_assessment_by_id(db, school_id, assessment_id)
    if not assessment.items:
        raise ValidationException("Cannot approve an assessment with zero questions.")

    assessment.status = "approved"
    assessment.version += 1
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="assessment.approved",
        entity_type="assessment",
        entity_id=assessment.id,
        metadata_json={
            "title": assessment.title,
            "version": assessment.version,
            "total_marks": assessment.total_marks,
            "items_count": len(assessment.items),
        },
    )

    return assessment
