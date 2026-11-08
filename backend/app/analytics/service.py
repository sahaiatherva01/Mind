import math
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from backend.app.identity.models import User, UserRole
from backend.app.academics.models import (
    Class,
    Section,
    Subject,
    TeacherAssignment,
    StudentEnrollment,
)
from backend.app.content.models import Question
from backend.app.assessments.models import (
    Assessment,
    AssessmentItem,
    Schedule,
    Attempt,
    StudentResponse,
    AssessmentStatus,
    AttemptStatus,
)
from backend.app.analytics.schemas import (
    QuestionAnalysis,
    AssessmentAnalytics,
    ClassAssessmentSummary,
    ClassAnalytics,
    TopicMastery,
    TeacherDashboardSummary,
)


class AnalyticsService:
    @staticmethod
    async def verify_teacher_class_access(
        db: AsyncSession, user: User, class_id: str
    ) -> bool:
        """Admins have access to all classes in tenant. Teachers only if assigned to a section."""
        if user.role == UserRole.ADMIN:
            return True
        if user.role != UserRole.TEACHER:
            return False

        q = (
            select(TeacherAssignment)
            .join(Section, TeacherAssignment.section_id == Section.id)
            .where(
                and_(
                    TeacherAssignment.school_id == user.school_id,
                    TeacherAssignment.teacher_id == user.id,
                    Section.class_id == class_id,
                )
            )
        )
        res = await db.execute(q)
        return res.scalars().first() is not None

    @staticmethod
    async def verify_teacher_assessment_access(
        db: AsyncSession, user: User, assessment: Assessment
    ) -> bool:
        """Admins have access to all assessments in tenant. Teachers only if assigned to class+subject."""
        if user.role == UserRole.ADMIN:
            return True
        if user.role != UserRole.TEACHER:
            return False

        q = (
            select(TeacherAssignment)
            .join(Section, TeacherAssignment.section_id == Section.id)
            .where(
                and_(
                    TeacherAssignment.school_id == user.school_id,
                    TeacherAssignment.teacher_id == user.id,
                    Section.class_id == assessment.class_id,
                    TeacherAssignment.subject_id == assessment.subject_id,
                )
            )
        )
        res = await db.execute(q)
        return res.scalars().first() is not None

    @staticmethod
    async def get_assessment_analytics(
        db: AsyncSession, user: User, assessment_id: str
    ) -> AssessmentAnalytics:
        stmt = (
            select(Assessment)
            .where(
                and_(
                    Assessment.id == assessment_id,
                    Assessment.school_id == user.school_id,
                )
            )
        )
        res = await db.execute(stmt)
        assessment = res.scalars().first()
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if not await AnalyticsService.verify_teacher_assessment_access(db, user, assessment):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this assessment analytics.",
            )

        # Total enrolled students in target class
        enrolled_stmt = (
            select(func.count(StudentEnrollment.id))
            .join(Section, StudentEnrollment.section_id == Section.id)
            .where(
                and_(
                    StudentEnrollment.school_id == user.school_id,
                    Section.class_id == assessment.class_id,
                )
            )
        )
        enrolled_res = await db.execute(enrolled_stmt)
        total_enrolled = enrolled_res.scalar() or 0

        # Fetch all submitted or timed out attempts
        attempts_stmt = (
            select(Attempt)
            .where(
                and_(
                    Attempt.assessment_id == assessment_id,
                    Attempt.school_id == user.school_id,
                    Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT]),
                )
            )
            .order_by(Attempt.total_score.desc())
        )
        attempts_res = await db.execute(attempts_stmt)
        attempts = list(attempts_res.scalars().all())
        submitted_count = len(attempts)

        scores = [att.total_score or 0.0 for att in attempts]
        max_marks = float(assessment.total_marks or 1.0)

        if scores:
            avg_score = sum(scores) / len(scores)
            avg_pct = (avg_score / max_marks) * 100
            scores_sorted = sorted(scores)
            mid = len(scores_sorted) // 2
            if len(scores_sorted) % 2 == 0:
                median_score = (scores_sorted[mid - 1] + scores_sorted[mid]) / 2.0
            else:
                median_score = scores_sorted[mid]
            high_score = max(scores)
            low_score = min(scores)
        else:
            avg_score = 0.0
            avg_pct = 0.0
            median_score = 0.0
            high_score = 0.0
            low_score = 0.0

        # Score distribution
        dist = {
            "0-20%": 0,
            "21-40%": 0,
            "41-60%": 0,
            "61-80%": 0,
            "81-100%": 0,
        }
        for s in scores:
            pct = (s / max_marks) * 100 if max_marks > 0 else 0
            if pct <= 20:
                dist["0-20%"] += 1
            elif pct <= 40:
                dist["21-40%"] += 1
            elif pct <= 60:
                dist["41-60%"] += 1
            elif pct <= 80:
                dist["61-80%"] += 1
            else:
                dist["81-100%"] += 1

        # Fetch assessment items with questions
        items_stmt = (
            select(AssessmentItem)
            .options(joinedload(AssessmentItem.question))
            .where(AssessmentItem.assessment_id == assessment_id)
            .order_by(AssessmentItem.position.asc())
        )
        items_res = await db.execute(items_stmt)
        items = list(items_res.scalars().all())

        # Question level analysis
        question_analyses: List[QuestionAnalysis] = []

        n_group = max(1, int(math.ceil(0.27 * len(attempts)))) if len(attempts) >= 4 else len(attempts)
        upper_attempt_ids = {att.id for att in attempts[:n_group]}
        lower_attempt_ids = {att.id for att in attempts[-n_group:]}

        for item in items:
            q = item.question
            item_marks = float(item.marks_override or (q.marks if q else 1))
            prompt_text = q.prompt if q else "Question prompt"
            item_type = q.type if q else "mcq"
            topic_str = (q.topic_tags[0] if q and q.topic_tags else None)

            resp_stmt = (
                select(StudentResponse)
                .where(StudentResponse.assessment_item_id == item.id)
            )
            resp_res = await db.execute(resp_stmt)
            responses = list(resp_res.scalars().all())

            total_resp = len(responses)

            def get_resp_score(r: StudentResponse) -> float:
                if r.manual_score is not None:
                    return float(r.manual_score)
                if r.auto_score is not None:
                    return float(r.auto_score)
                return 0.0

            correct_resp = sum(1 for r in responses if get_resp_score(r) >= (item_marks * 0.9))
            avg_marks = sum(get_resp_score(r) for r in responses) / total_resp if total_resp > 0 else 0.0
            acc_pct = (avg_marks / item_marks) * 100 if item_marks > 0 else 0.0

            # Discrimination calculation
            if len(attempts) >= 4:
                upper_resp = [r for r in responses if r.attempt_id in upper_attempt_ids]
                lower_resp = [r for r in responses if r.attempt_id in lower_attempt_ids]

                upper_acc = (
                    sum(get_resp_score(r) for r in upper_resp) / (len(upper_resp) * item_marks)
                    if upper_resp and item_marks > 0
                    else 0.0
                )
                lower_acc = (
                    sum(get_resp_score(r) for r in lower_resp) / (len(lower_resp) * item_marks)
                    if lower_resp and item_marks > 0
                    else 0.0
                )
                disc_index = round(upper_acc - lower_acc, 2)
            else:
                disc_index = 0.40  # Default baseline before statistical sample

            if disc_index >= 0.40:
                interp = "Excellent discrimination"
            elif disc_index >= 0.30:
                interp = "Good discrimination"
            elif disc_index >= 0.20:
                interp = "Acceptable discrimination"
            else:
                interp = "Review needed (low discrimination)"

            question_analyses.append(
                QuestionAnalysis(
                    item_id=item.id,
                    item_type=item_type,
                    prompt=prompt_text,
                    max_marks=item_marks,
                    topic=topic_str,
                    total_responses=total_resp,
                    correct_responses=correct_resp,
                    average_marks_awarded=round(avg_marks, 2),
                    accuracy_pct=round(acc_pct, 1),
                    discrimination_index=disc_index,
                    interpretation=interp,
                )
            )

        # Subject name lookup
        subj_stmt = select(Subject.name).where(Subject.id == assessment.subject_id)
        subj_res = await db.execute(subj_stmt)
        subject_name = subj_res.scalar() or "Subject"

        return AssessmentAnalytics(
            assessment_id=assessment.id,
            title=assessment.title,
            subject=subject_name,
            total_enrolled=total_enrolled,
            submitted_count=submitted_count,
            total_max_marks=max_marks,
            average_score=round(avg_score, 2),
            average_score_pct=round(avg_pct, 1),
            median_score=round(median_score, 2),
            highest_score=round(high_score, 2),
            lowest_score=round(low_score, 2),
            score_distribution=dist,
            question_analysis=question_analyses,
        )

    @staticmethod
    async def get_class_analytics(
        db: AsyncSession, user: User, class_id: str
    ) -> ClassAnalytics:
        class_stmt = (
            select(Class)
            .where(and_(Class.id == class_id, Class.school_id == user.school_id))
        )
        c_res = await db.execute(class_stmt)
        target_class = c_res.scalars().first()
        if not target_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found.",
            )

        if not await AnalyticsService.verify_teacher_class_access(db, user, class_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this class analytics.",
            )

        # Total students enrolled in class
        students_stmt = (
            select(func.count(StudentEnrollment.id))
            .join(Section, StudentEnrollment.section_id == Section.id)
            .where(
                and_(
                    StudentEnrollment.school_id == user.school_id,
                    Section.class_id == class_id,
                )
            )
        )
        s_res = await db.execute(students_stmt)
        total_students = s_res.scalar() or 0

        # Assessments for this class
        assessments_stmt = (
            select(Assessment)
            .where(
                and_(
                    Assessment.class_id == class_id,
                    Assessment.school_id == user.school_id,
                    Assessment.status.in_([
                        AssessmentStatus.PUBLISHED,
                        AssessmentStatus.SCHEDULED,
                        AssessmentStatus.EVALUATED,
                        AssessmentStatus.RESULTS_RELEASED,
                    ]),
                )
            )
        )
        a_res = await db.execute(assessments_stmt)
        assessments = list(a_res.scalars().all())

        total_assessments = len(assessments)
        total_attempts = 0
        total_score_pct_sum = 0.0
        ass_summaries: List[ClassAssessmentSummary] = []

        for ass in assessments:
            att_stmt = (
                select(Attempt)
                .where(
                    and_(
                        Attempt.assessment_id == ass.id,
                        Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT]),
                    )
                )
            )
            att_res = await db.execute(att_stmt)
            atts = list(att_res.scalars().all())
            sub_count = len(atts)
            total_attempts += sub_count

            if sub_count > 0 and ass.total_marks > 0:
                avg_m = sum(a.total_score or 0.0 for a in atts) / sub_count
                avg_p = (avg_m / ass.total_marks) * 100
            else:
                avg_p = 0.0

            total_score_pct_sum += avg_p

            subj_stmt = select(Subject.name).where(Subject.id == ass.subject_id)
            subj_res = await db.execute(subj_stmt)
            s_name = subj_res.scalar() or "Subject"

            ass_summaries.append(
                ClassAssessmentSummary(
                    assessment_id=ass.id,
                    title=ass.title,
                    subject=s_name,
                    submitted_count=sub_count,
                    average_score_pct=round(avg_p, 1),
                    status=ass.status,
                )
            )

        avg_class_score_pct = (
            round(total_score_pct_sum / total_assessments, 1)
            if total_assessments > 0
            else 0.0
        )
        potential_total = total_students * total_assessments
        completion_rate = (
            round((total_attempts / potential_total) * 100, 1)
            if potential_total > 0
            else 0.0
        )

        return ClassAnalytics(
            class_id=target_class.id,
            class_name=target_class.name,
            total_students=total_students,
            total_assessments=total_assessments,
            total_attempts=total_attempts,
            average_score_pct=avg_class_score_pct,
            completion_rate_pct=completion_rate,
            assessments=ass_summaries,
        )

    @staticmethod
    async def get_topic_analytics(
        db: AsyncSession, user: User, subject_id: Optional[str] = None
    ) -> List[TopicMastery]:
        query = (
            select(
                Question.topic_tags,
                Subject.name.label("subject_name"),
                AssessmentItem.marks_override,
                Question.marks.label("q_marks"),
                StudentResponse.auto_score,
                StudentResponse.manual_score,
            )
            .join(AssessmentItem, Question.id == AssessmentItem.question_id)
            .join(Assessment, AssessmentItem.assessment_id == Assessment.id)
            .join(Subject, Assessment.subject_id == Subject.id)
            .outerjoin(StudentResponse, AssessmentItem.id == StudentResponse.assessment_item_id)
            .where(Assessment.school_id == user.school_id)
        )

        if subject_id:
            query = query.where(Assessment.subject_id == subject_id)

        if user.role == UserRole.TEACHER:
            assigned_subj_stmt = (
                select(TeacherAssignment.subject_id)
                .where(
                    and_(
                        TeacherAssignment.school_id == user.school_id,
                        TeacherAssignment.teacher_id == user.id,
                    )
                )
                .distinct()
            )
            assigned_subj_res = await db.execute(assigned_subj_stmt)
            allowed_subject_ids = list(assigned_subj_res.scalars().all())
            query = query.where(Assessment.subject_id.in_(allowed_subject_ids))

        res = await db.execute(query)
        rows = res.all()

        topic_data: Dict[str, Dict] = {}
        for topic_tags, subj_name, marks_override, q_marks, auto_score, manual_score in rows:
            if not topic_tags:
                continue
            topic = topic_tags[0] if isinstance(topic_tags, list) and topic_tags else str(topic_tags)
            key = f"{subj_name}::{topic}"
            if key not in topic_data:
                topic_data[key] = {
                    "topic": topic,
                    "subject": subj_name,
                    "items": set(),
                    "total_attempts": 0,
                    "total_awarded": 0.0,
                    "total_possible": 0.0,
                }
            item_mark = float(marks_override or q_marks or 1.0)
            score_awarded = manual_score if manual_score is not None else auto_score
            if score_awarded is not None:
                topic_data[key]["total_attempts"] += 1
                topic_data[key]["total_awarded"] += float(score_awarded)
                topic_data[key]["total_possible"] += item_mark

        results: List[TopicMastery] = []
        for key, d in topic_data.items():
            if d["total_possible"] > 0:
                mastery_pct = round((d["total_awarded"] / d["total_possible"]) * 100, 1)
            else:
                mastery_pct = 75.0

            if mastery_pct >= 80.0:
                status_str = "mastered"
            elif mastery_pct >= 60.0:
                status_str = "proficient"
            else:
                status_str = "needs_reinforcement"

            results.append(
                TopicMastery(
                    topic=d["topic"],
                    subject=d["subject"],
                    total_items=len(d["items"]) or 1,
                    total_attempts=d["total_attempts"],
                    average_mastery_pct=mastery_pct,
                    status=status_str,
                )
            )

        results.sort(key=lambda x: x.average_mastery_pct)
        return results

    @staticmethod
    async def get_teacher_dashboard_summary(
        db: AsyncSession, user: User
    ) -> TeacherDashboardSummary:
        if user.role != UserRole.TEACHER:
            return TeacherDashboardSummary(
                assigned_classes_count=0,
                active_assessments_count=0,
                pending_evaluations_count=0,
                total_graded_submissions=0,
            )

        # Assigned classes/sections count
        assign_stmt = (
            select(func.count(TeacherAssignment.id))
            .where(
                and_(
                    TeacherAssignment.school_id == user.school_id,
                    TeacherAssignment.teacher_id == user.id,
                )
            )
        )
        assign_res = await db.execute(assign_stmt)
        assigned_count = assign_res.scalar() or 0

        # Teacher's assessments
        ass_stmt = (
            select(Assessment.id)
            .where(
                and_(
                    Assessment.school_id == user.school_id,
                    Assessment.creator_id == user.id,
                )
            )
        )
        ass_res = await db.execute(ass_stmt)
        assessment_ids = list(ass_res.scalars().all())

        # Active assessments count
        active_stmt = (
            select(func.count(Assessment.id))
            .where(
                and_(
                    Assessment.school_id == user.school_id,
                    Assessment.creator_id == user.id,
                    Assessment.status.in_([
                        AssessmentStatus.PUBLISHED,
                        AssessmentStatus.SCHEDULED,
                    ]),
                )
            )
        )
        active_res = await db.execute(active_stmt)
        active_count = active_res.scalar() or 0

        # Pending subjective evaluations count
        if assessment_ids:
            pending_stmt = (
                select(func.count(StudentResponse.id))
                .join(Attempt, StudentResponse.attempt_id == Attempt.id)
                .join(AssessmentItem, StudentResponse.assessment_item_id == AssessmentItem.id)
                .join(Question, AssessmentItem.question_id == Question.id)
                .where(
                    and_(
                        Attempt.assessment_id.in_(assessment_ids),
                        StudentResponse.manual_score.is_(None),
                        Question.type.in_([
                            "very_short_answer", "short_answer", "medium_answer", "long_answer",
                            "definition_based", "reasoning_based", "derivation_based",
                            "algorithm_writing", "program_writing",
                        ]),
                    )
                )
            )
            pending_res = await db.execute(pending_stmt)
            pending_count = pending_res.scalar() or 0

            graded_stmt = (
                select(func.count(Attempt.id))
                .where(
                    and_(
                        Attempt.assessment_id.in_(assessment_ids),
                        Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT]),
                        Attempt.total_score.isnot(None),
                    )
                )
            )
            graded_res = await db.execute(graded_stmt)
            graded_count = graded_res.scalar() or 0
        else:
            pending_count = 0
            graded_count = 0

        return TeacherDashboardSummary(
            assigned_classes_count=assigned_count,
            active_assessments_count=active_count,
            pending_evaluations_count=pending_count,
            total_graded_submissions=graded_count,
        )
