"""
Assessment Delivery & Attempt Lifecycle Service
Enforces server-authoritative time, immutable published versions, no answer key leakage,
and idempotent autosave/submit.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import (
    NotFoundException,
    ValidationException,
    ForbiddenException,
    ConflictException,
)
from backend.app.assessments.models import (
    Assessment,
    AssessmentItem,
    Schedule,
    Attempt,
    StudentResponse,
)
from backend.app.academics.models import StudentEnrollment, Class, Section
from backend.app.content.models import Question
from backend.app.evaluation.scoring import evaluate_objective_response
from backend.app.audit.service import record_audit_event


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ------------------- TEACHER PUBLISH & SCHEDULE -------------------

async def publish_or_schedule_assessment(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    starts_at: datetime,
    ends_at: datetime,
    timezone_str: str = "Asia/Kolkata",
    duration_minutes: Optional[int] = None,
    max_attempts: int = 1,
    result_release_mode: str = "manual_by_teacher",
    result_release_at: Optional[datetime] = None,
    allow_late_submission: bool = False,
    actor_id: Optional[str] = None,
) -> Assessment:
    stmt = (
        select(Assessment)
        .options(selectinload(Assessment.items))
        .where(Assessment.id == assessment_id, Assessment.school_id == school_id)
    )
    res = await db.execute(stmt)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise NotFoundException("Assessment", assessment_id)

    if assessment.status != "approved":
        raise ValidationException("Teacher approval is mandatory before publishing an assessment.")

    if not assessment.items:
        raise ValidationException("Cannot publish an assessment with zero questions.")

    now_utc = datetime.now(timezone.utc)
    starts_at_utc = ensure_utc(starts_at)
    ends_at_utc = ensure_utc(ends_at)
    if ends_at_utc <= starts_at_utc:
        raise ValidationException("Assessment end time must be after start time.")

    # Determine status: published (if active now) or scheduled (if future)
    new_status = "published" if starts_at_utc <= now_utc else "scheduled"

    # Upsert schedule
    sched_stmt = select(Schedule).where(Schedule.assessment_id == assessment_id)
    res_s = await db.execute(sched_stmt)
    schedule = res_s.scalar_one_or_none()

    if not schedule:
        schedule = Schedule(
            assessment_id=assessment_id,
            starts_at=starts_at,
            ends_at=ends_at,
            timezone=timezone_str,
            duration_minutes=duration_minutes,
            max_attempts=max_attempts,
            allow_late_submission=allow_late_submission,
            result_release_mode=result_release_mode,
            result_release_at=result_release_at,
        )
        db.add(schedule)
    else:
        schedule.starts_at = starts_at
        schedule.ends_at = ends_at
        schedule.timezone = timezone_str
        schedule.duration_minutes = duration_minutes
        schedule.max_attempts = max_attempts
        schedule.allow_late_submission = allow_late_submission
        schedule.result_release_mode = result_release_mode
        schedule.result_release_at = result_release_at

    assessment.status = new_status
    await db.flush()

    # Trigger notifications for enrolled students in section
    if new_status in ("published", "scheduled"):
        from backend.app.academics.models import StudentEnrollment
        from backend.app.notifications.service import send_bulk_notifications
        enr_res = await db.execute(
            select(StudentEnrollment.student_id).where(
                StudentEnrollment.school_id == school_id,
                StudentEnrollment.section_id == assessment.section_id,
                StudentEnrollment.status == "active",
            )
        )
        enrolled_student_ids = list(enr_res.scalars().all())
        if enrolled_student_ids:
            await send_bulk_notifications(
                db=db,
                school_id=school_id,
                user_ids=enrolled_student_ids,
                title=f"New Assessment Assigned: {assessment.title}",
                message=f"A new {assessment.type.replace('_', ' ')} has been published for your section. Check upcoming tests to attempt.",
                type="assignment_published",
                link_url="/student/assessments",
                metadata_json={"assessment_id": assessment.id, "type": assessment.type},
            )

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action=f"assessment.{new_status}",
        entity_type="assessment",
        entity_id=assessment.id,
        metadata_json={
            "status": new_status,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "release_mode": result_release_mode,
        },
    )

    return assessment


# ------------------- STUDENT ASSESSMENT ACCESS -------------------

async def list_student_assignments(
    db: AsyncSession,
    school_id: str,
    student_id: str,
) -> List[Dict[str, Any]]:
    """Returns published assessments for the student's enrolled classes without answer keys."""
    enr_stmt = select(StudentEnrollment).where(
        StudentEnrollment.school_id == school_id,
        StudentEnrollment.student_id == student_id,
        StudentEnrollment.status == "active",
    )
    enr_res = await db.execute(enr_stmt)
    enrollments = enr_res.scalars().all()

    if not enrollments:
        return []

    # Filter assessments published or scheduled for these classes/sections
    results = []
    now_utc = datetime.now(timezone.utc)

    for enr in enrollments:
        stmt = (
            select(Assessment)
            .options(selectinload(Assessment.schedule))
            .where(
                Assessment.school_id == school_id,
                Assessment.class_id == enr.class_id,
                Assessment.section_id == enr.section_id,
                Assessment.status.in_(["published", "scheduled", "closed", "evaluated", "results_released"]),
            )
        )
        res = await db.execute(stmt)
        assessments = res.scalars().all()

        for a in assessments:
            # Check student attempt if any
            att_stmt = select(Attempt).where(
                Attempt.assessment_id == a.id, Attempt.student_id == student_id
            )
            att_res = await db.execute(att_stmt)
            attempt = att_res.scalar_one_or_none()

            sched = a.schedule
            results.append({
                "id": a.id,
                "title": a.title,
                "type": a.type,
                "status": a.status,
                "total_marks": a.total_marks,
                "instructions": a.instructions,
                "starts_at": sched.starts_at if sched else None,
                "ends_at": sched.ends_at if sched else None,
                "duration_minutes": sched.duration_minutes if sched else None,
                "has_attempted": attempt is not None,
                "attempt_status": attempt.status if attempt else "not_started",
                "attempt_id": attempt.id if attempt else None,
                "is_released": attempt.is_released if attempt else False,
            })

    return results


async def get_student_assessment_instructions(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    student_id: str,
) -> Dict[str, Any]:
    stmt = (
        select(Assessment)
        .options(selectinload(Assessment.schedule))
        .where(Assessment.id == assessment_id, Assessment.school_id == school_id)
    )
    res = await db.execute(stmt)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise NotFoundException("Assessment", assessment_id)

    if assessment.status not in ("published", "scheduled", "results_released"):
        raise ForbiddenException("This assessment is not currently available for student attempts.")

    sched = assessment.schedule
    return {
        "id": assessment.id,
        "title": assessment.title,
        "type": assessment.type,
        "total_marks": assessment.total_marks,
        "instructions": assessment.instructions,
        "starts_at": sched.starts_at if sched else None,
        "ends_at": sched.ends_at if sched else None,
        "duration_minutes": sched.duration_minutes if sched else None,
        "max_attempts": sched.max_attempts if sched else 1,
    }


async def start_student_attempt(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    student_id: str,
) -> Tuple[Attempt, List[Dict[str, Any]]]:
    """
    Starts student attempt. Enforces server time and returns questions WITHOUT answer keys.
    """
    stmt = (
        select(Assessment)
        .options(
            selectinload(Assessment.schedule),
            selectinload(Assessment.items).selectinload(AssessmentItem.question),
        )
        .where(Assessment.id == assessment_id, Assessment.school_id == school_id)
    )
    res = await db.execute(stmt)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise NotFoundException("Assessment", assessment_id)

    sched = assessment.schedule
    now_utc = datetime.now(timezone.utc)

    if sched:
        starts_at = ensure_utc(sched.starts_at)
        ends_at = ensure_utc(sched.ends_at)
        if starts_at and now_utc < starts_at:
            raise ValidationException("This assessment has not started yet.")
        if ends_at and now_utc > ends_at and not sched.allow_late_submission:
            raise ValidationException("The submission window for this assessment has closed.")

    # Check existing attempt
    att_stmt = select(Attempt).where(
        Attempt.assessment_id == assessment_id, Attempt.student_id == student_id
    )
    att_res = await db.execute(att_stmt)
    existing_attempt = att_res.scalar_one_or_none()

    if existing_attempt:
        if existing_attempt.status == "in_progress":
            attempt = existing_attempt
        else:
            raise ConflictException("You have already submitted this assessment. Maximum attempts reached.")
    else:
        attempt = Attempt(
            school_id=school_id,
            assessment_id=assessment_id,
            student_id=student_id,
            attempt_number=1,
            started_at=now_utc,
            status="in_progress",
            max_score=float(assessment.total_marks),
        )
        db.add(attempt)
        await db.flush()

        await record_audit_event(
            db=db,
            school_id=school_id,
            actor_id=student_id,
            action="attempt.started",
            entity_type="attempt",
            entity_id=attempt.id,
        )

    # Sanitize questions: STRICTLY STRIP ANSWER KEYS & RATIONALES
    safe_questions = []
    for item in assessment.items:
        q = item.question
        safe_questions.append({
            "item_id": item.id,
            "position": item.position,
            "marks": item.marks_override if item.marks_override is not None else q.marks,
            "type": q.type,
            "category": q.category,
            "prompt": q.prompt,
            "content_data": q.content_data,  # Contains choices/match pairs/code snippet
            # NO answer_data, expected_answer, or rationale!
        })

    return attempt, safe_questions


async def autosave_student_response(
    db: AsyncSession,
    school_id: str,
    attempt_id: str,
    item_id: str,
    student_id: str,
    answer_json: Dict[str, Any],
) -> StudentResponse:
    stmt = (
        select(Attempt)
        .options(selectinload(Attempt.assessment).selectinload(Assessment.schedule))
        .where(Attempt.id == attempt_id, Attempt.student_id == student_id)
    )
    res = await db.execute(stmt)
    attempt = res.scalar_one_or_none()
    if not attempt:
        raise NotFoundException("Attempt", attempt_id)

    if attempt.status != "in_progress":
        raise ValidationException("Cannot autosave response: attempt is already submitted or closed.")

    # Server time limit check with 60s network grace period
    sched = attempt.assessment.schedule
    now_utc = datetime.now(timezone.utc)
    if sched and sched.duration_minutes:
        max_duration = timedelta(minutes=sched.duration_minutes, seconds=60)
        started_at = ensure_utc(attempt.started_at)
        if started_at and (now_utc - started_at > max_duration):
            attempt.status = "timed_out"
            await db.flush()
            raise ValidationException("Attempt time limit expired.")

    # Upsert response
    resp_stmt = select(StudentResponse).where(
        StudentResponse.attempt_id == attempt_id,
        StudentResponse.assessment_item_id == item_id,
    )
    resp_res = await db.execute(resp_stmt)
    resp_record = resp_res.scalar_one_or_none()

    if not resp_record:
        resp_record = StudentResponse(
            attempt_id=attempt_id,
            assessment_item_id=item_id,
            answer_json=answer_json,
            saved_at=datetime.now(timezone.utc),
        )
        db.add(resp_record)
    else:
        resp_record.answer_json = answer_json
        resp_record.saved_at = datetime.now(timezone.utc)

    await db.flush()
    return resp_record


async def submit_student_attempt(
    db: AsyncSession,
    school_id: str,
    attempt_id: str,
    student_id: str,
) -> Attempt:
    """
    Idempotent transactional submit:
    Calculates deterministic objective scores and applies result release policies.
    """
    stmt = (
        select(Attempt)
        .options(
            selectinload(Attempt.assessment).selectinload(Assessment.schedule),
            selectinload(Attempt.assessment).selectinload(Assessment.items).selectinload(AssessmentItem.question),
            selectinload(Attempt.responses),
        )
        .where(Attempt.id == attempt_id, Attempt.student_id == student_id)
    )
    res = await db.execute(stmt)
    attempt = res.scalar_one_or_none()
    if not attempt:
        raise NotFoundException("Attempt", attempt_id)

    # Idempotent: If already submitted, return safely
    if attempt.status in ("submitted", "timed_out"):
        return attempt

    attempt.status = "submitted"
    attempt.submitted_at = datetime.now(timezone.utc)

    # Automatic deterministic objective grading
    assessment = attempt.assessment
    items_by_id = {item.id: item for item in assessment.items}
    responses_by_item_id = {r.assessment_item_id: r for r in attempt.responses}

    total_objective_score = 0.0
    has_subjective_items = False

    for item in assessment.items:
        q = item.question
        resp = responses_by_item_id.get(item.id)
        max_m = float(item.marks_override if item.marks_override is not None else q.marks)

        if resp:
            score, is_auto = evaluate_objective_response(q, resp.answer_json, max_m)
            if is_auto:
                resp.auto_score = score
                total_objective_score += score
            else:
                has_subjective_items = True
        else:
            # Unanswered
            score, is_auto = evaluate_objective_response(q, {}, max_m)
            if is_auto:
                empty_resp = StudentResponse(
                    attempt_id=attempt.id,
                    assessment_item_id=item.id,
                    answer_json={},
                    auto_score=0.0,
                )
                db.add(empty_resp)
            else:
                has_subjective_items = True

    attempt.total_score = total_objective_score

    # Apply result release policy
    sched = assessment.schedule
    if sched and sched.result_release_mode == "immediate_on_submit" and not has_subjective_items:
        attempt.is_released = True
        attempt.released_at = datetime.now(timezone.utc)

    await db.flush()

    # Notify teacher/creator of submission
    from backend.app.notifications.service import create_notification
    from backend.app.identity.models import User
    student_obj = await db.get(User, student_id)
    student_name = student_obj.full_name if student_obj else "A student"
    try:
        await create_notification(
            db=db,
            school_id=school_id,
            user_id=assessment.creator_id,
            title=f"Submission: {assessment.title}",
            message=f"{student_name} submitted their attempt for '{assessment.title}'.",
            type="submission_received",
            link_url="/teacher/evaluations",
            metadata_json={"attempt_id": attempt.id, "student_id": student_id, "assessment_id": assessment.id},
        )
    except Exception as err:
        logger.warning(f"Could not dispatch submission notification: {err}")

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=student_id,
        action="attempt.submitted",
        entity_type="attempt",
        entity_id=attempt.id,
        metadata_json={
            "submitted_at": attempt.submitted_at.isoformat(),
            "auto_score": attempt.total_score,
            "is_released": attempt.is_released,
        },
    )

    return attempt


# ------------------- TEACHER EVALUATION & RESULT RELEASE -------------------

async def get_teacher_evaluation_queue(
    db: AsyncSession,
    school_id: str,
    teacher_id: str,
) -> List[Dict[str, Any]]:
    """Lists student responses awaiting teacher subjective evaluation."""
    stmt = (
        select(StudentResponse)
        .options(
            selectinload(StudentResponse.attempt).selectinload(Attempt.student),
            selectinload(StudentResponse.assessment_item).selectinload(AssessmentItem.question),
            selectinload(StudentResponse.assessment_item).selectinload(AssessmentItem.assessment),
        )
        .join(Attempt, StudentResponse.attempt_id == Attempt.id)
        .join(Assessment, Attempt.assessment_id == Assessment.id)
        .where(
            Assessment.school_id == school_id,
            Attempt.status == "submitted",
            StudentResponse.auto_score.is_(None),  # Subjective items
            StudentResponse.manual_score.is_(None),  # Unevaluated
        )
    )
    res = await db.execute(stmt)
    pending = res.scalars().all()

    queue = []
    for r in pending:
        q = r.assessment_item.question
        queue.append({
            "response_id": r.id,
            "attempt_id": r.attempt_id,
            "student_name": r.attempt.student.full_name,
            "assessment_title": r.assessment_item.assessment.title,
            "question_prompt": q.prompt,
            "question_type": q.type,
            "max_marks": r.assessment_item.marks_override or q.marks,
            "student_answer": r.answer_json,
            "marking_scheme": q.answer_data.get("marking_scheme") if q.answer_data else None,
            "expected_answer": q.answer_data.get("expected_answer") if q.answer_data else None,
        })
    return queue


async def grade_student_response(
    db: AsyncSession,
    school_id: str,
    response_id: str,
    teacher_id: str,
    manual_score: float,
    teacher_feedback: Optional[str] = None,
) -> StudentResponse:
    stmt = (
        select(StudentResponse)
        .options(selectinload(StudentResponse.attempt))
        .where(StudentResponse.id == response_id)
    )
    res = await db.execute(stmt)
    resp = res.scalar_one_or_none()
    if not resp:
        raise NotFoundException("StudentResponse", response_id)

    resp.manual_score = manual_score
    resp.teacher_feedback = teacher_feedback

    # Recalculate attempt total score
    att = resp.attempt
    all_resps = await db.execute(select(StudentResponse).where(StudentResponse.attempt_id == att.id))
    total = sum(
        (r.manual_score if r.manual_score is not None else (r.auto_score or 0.0))
        for r in all_resps.scalars().all()
    )
    att.total_score = total
    await db.flush()

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=teacher_id,
        action="evaluation.graded",
        entity_type="student_response",
        entity_id=response_id,
        metadata_json={"score": manual_score},
    )

    return resp


async def release_assessment_results(
    db: AsyncSession,
    school_id: str,
    assessment_id: str,
    actor_id: str,
) -> int:
    """Releases marks, answer keys, and model solutions to all student attempts."""
    stmt = select(Attempt).where(
        Attempt.assessment_id == assessment_id,
        Attempt.school_id == school_id,
        Attempt.status == "submitted",
    )
    res = await db.execute(stmt)
    attempts = res.scalars().all()

    now_utc = datetime.now(timezone.utc)
    for att in attempts:
        att.is_released = True
        att.released_at = now_utc

    # Update assessment status to results_released
    asmt_stmt = select(Assessment).where(Assessment.id == assessment_id, Assessment.school_id == school_id)
    asmt_res = await db.execute(asmt_stmt)
    asmt = asmt_res.scalar_one()
    asmt.status = "results_released"

    await db.flush()

    # Notify students who attempted the assessment that results are released
    from backend.app.notifications.service import send_bulk_notifications
    student_ids = list({att.student_id for att in attempts})
    if student_ids:
        try:
            await send_bulk_notifications(
                db=db,
                school_id=school_id,
                user_ids=student_ids,
                title=f"Results Released: {asmt.title}",
                message=f"Results and teacher feedback for '{asmt.title}' are now available. Review your marks and answers.",
                type="results_released",
                link_url="/student/results",
                metadata_json={"assessment_id": assessment_id},
            )
        except Exception as err:
            logger.warning(f"Could not dispatch results released notifications: {err}")

    await record_audit_event(
        db=db,
        school_id=school_id,
        actor_id=actor_id,
        action="assessment.results_released",
        entity_type="assessment",
        entity_id=assessment_id,
        metadata_json={"attempts_released": len(attempts)},
    )

    return len(attempts)


async def get_student_attempt_result(
    db: AsyncSession,
    school_id: str,
    attempt_id: str,
    student_id: str,
) -> Dict[str, Any]:
    stmt = (
        select(Attempt)
        .options(
            selectinload(Attempt.assessment),
            selectinload(Attempt.responses).selectinload(StudentResponse.assessment_item).selectinload(AssessmentItem.question),
        )
        .where(Attempt.id == attempt_id, Attempt.student_id == student_id)
    )
    res = await db.execute(stmt)
    attempt = res.scalar_one_or_none()
    if not attempt:
        raise NotFoundException("Attempt", attempt_id)

    # Enforce non-negotiable #6: If results are not released, hide rationales and scores!
    if not attempt.is_released:
        raise ForbiddenException("Results for this assessment have not been released by your teacher yet.")

    responses_data = []
    for r in attempt.responses:
        q = r.assessment_item.question
        responses_data.append({
            "item_id": r.assessment_item_id,
            "prompt": q.prompt,
            "type": q.type,
            "student_answer": r.answer_json,
            "auto_score": r.auto_score,
            "manual_score": r.manual_score,
            "teacher_feedback": r.teacher_feedback,
            "expected_answer": q.answer_data.get("expected_answer") if q.answer_data else None,
            "marking_scheme": q.answer_data.get("marking_scheme") if q.answer_data else None,
            "rationale": q.answer_data.get("rationale") if q.answer_data else None,
        })

    return {
        "attempt_id": attempt.id,
        "assessment_title": attempt.assessment.title,
        "total_score": attempt.total_score,
        "max_score": attempt.max_score,
        "submitted_at": attempt.submitted_at,
        "responses": responses_data,
    }
