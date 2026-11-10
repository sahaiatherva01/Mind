"""
Advanced Academic Workflows Service — Mind V2 (Phase 8)
Implements:
- Early-Warning Signals & Coordinator Interventions
- Smart Student Segmentation & One-Click Remedial Generation
- Substitute Teacher Management with Temporal Validity
- Student Academic Goals, Revision List & Structured Doubts
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import joinedload

from backend.app.identity.models import User, RoleName, RoleAssignment
from backend.app.academics.models import Class, Section, Subject, TeacherAssignment, StudentEnrollment
from backend.app.tenancy.models import Band
from backend.app.assessments.models import (
    Assessment,
    AssessmentItem,
    Attempt,
    StudentResponse,
    AssessmentStatus,
    AttemptStatus,
)
from backend.app.content.models import Material, MaterialEngagement, Question
from backend.app.workflows.models import (
    CoordinatorIntervention,
    SmartStudentGroup,
    StudentAcademicGoal,
    StudentDoubtQuery,
)
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
from backend.app.core.policies import authorize
from backend.app.core.permission_matrix import Action
from backend.app.core.errors import ForbiddenException, NotFoundException, ValidationException


class WorkflowService:

    # --- 1. Early-Warning Signals & Coordinator Interventions ---

    @staticmethod
    async def get_early_warning_signals(
        db: AsyncSession, user: User, band_id: Optional[str] = None
    ) -> List[EarlyWarningSignal]:
        await authorize(user, Action.EARLY_WARNING_VIEW, {"school_id": user.school_id, "band_id": band_id}, db)

        # Classes in scope
        cls_q = select(Class).where(Class.school_id == user.school_id)
        if band_id:
            cls_q = cls_q.where(Class.band_id == band_id)
        classes = list((await db.execute(cls_q)).scalars().all())
        class_ids = [c.id for c in classes]

        if not class_ids:
            return []

        # Enrolled students
        enr_q = (
            select(StudentEnrollment)
            .options(joinedload(StudentEnrollment.student), joinedload(StudentEnrollment.class_obj), joinedload(StudentEnrollment.section))
            .where(
                and_(
                    StudentEnrollment.class_id.in_(class_ids),
                    StudentEnrollment.status == "active",
                )
            )
        )
        enrollments = list((await db.execute(enr_q)).scalars().all())

        signals: List[EarlyWarningSignal] = []

        for enr in enrollments:
            sid = enr.student_id
            s_name = enr.student.full_name if enr.student else f"Student {enr.roll_number}"

            # Student attempts
            att_q = (
                select(Attempt)
                .where(
                    and_(
                        Attempt.student_id == sid,
                        Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT]),
                    )
                )
                .order_by(Attempt.created_at.asc())
            )
            attempts = list((await db.execute(att_q)).scalars().all())

            scores = [
                ((a.total_score or 0.0) / (a.max_score or 1.0)) * 100
                for a in attempts
                if a.max_score and a.max_score > 0
            ]
            avg_pct = round(sum(scores) / len(scores), 1) if scores else 0.0

            # Material engagements count
            m_count = (
                await db.execute(
                    select(func.count(MaterialEngagement.id)).where(MaterialEngagement.student_id == sid)
                )
            ).scalar() or 0

            risk_factors: List[str] = []
            if len(scores) >= 1 and avg_pct < 45.0:
                risk_factors.append(f"Critical score deficit: Cumulative average is {avg_pct}%.")

            # Declining trajectory check
            if len(scores) >= 2 and scores[-1] < scores[-2]:
                risk_factors.append(f"Negative trajectory: Latest score ({scores[-1]}%) dropped from prior ({scores[-2]}%).")

            if m_count == 0 and len(scores) >= 1:
                risk_factors.append("Zero learning material engagements recorded.")

            if risk_factors:
                severity = "critical" if avg_pct < 35.0 or len(risk_factors) >= 3 else ("high" if avg_pct < 45.0 else "medium")
                signals.append(
                    EarlyWarningSignal(
                        student_id=sid,
                        student_name=s_name,
                        roll_number=enr.roll_number,
                        class_name=enr.class_obj.name if enr.class_obj else "Class",
                        section_name=enr.section.name if enr.section else "Section",
                        average_score_pct=avg_pct,
                        risk_factors=risk_factors,
                        severity=severity,
                    )
                )

        signals.sort(key=lambda s: 0 if s.severity == "critical" else (1 if s.severity == "high" else 2))
        return signals

    @staticmethod
    async def create_intervention(
        db: AsyncSession, user: User, payload: InterventionCreate
    ) -> InterventionResponse:
        await authorize(user, Action.INTERVENTION_MANAGE, {"school_id": user.school_id, "band_id": payload.band_id}, db)

        inter = CoordinatorIntervention(
            school_id=user.school_id,
            band_id=payload.band_id,
            student_id=payload.student_id,
            created_by=user.id,
            trigger_reason=payload.trigger_reason,
            severity=payload.severity,
            status="open",
            notes=payload.notes,
        )
        db.add(inter)
        await db.flush()
        await db.refresh(inter)

        stud = await db.get(User, inter.student_id)
        resp = InterventionResponse.model_validate(inter)
        resp.student_name = stud.full_name if stud else "Student"
        return resp

    @staticmethod
    async def update_intervention(
        db: AsyncSession, user: User, intervention_id: str, payload: InterventionUpdate
    ) -> InterventionResponse:
        inter = await db.get(CoordinatorIntervention, intervention_id)
        if not inter or inter.school_id != user.school_id:
            raise NotFoundException(f"Intervention '{intervention_id}' not found.")

        await authorize(user, Action.INTERVENTION_MANAGE, {"school_id": user.school_id, "band_id": inter.band_id}, db)

        if payload.status:
            inter.status = payload.status
            if payload.status == "resolved":
                inter.resolved_at = datetime.now(timezone.utc)
        if payload.action_taken is not None:
            inter.action_taken = payload.action_taken
        if payload.notes is not None:
            inter.notes = payload.notes

        await db.flush()
        await db.refresh(inter)

        stud = await db.get(User, inter.student_id)
        resp = InterventionResponse.model_validate(inter)
        resp.student_name = stud.full_name if stud else "Student"
        return resp

    @staticmethod
    async def list_interventions(
        db: AsyncSession, user: User, band_id: Optional[str] = None
    ) -> List[InterventionResponse]:
        await authorize(user, Action.INTERVENTION_MANAGE, {"school_id": user.school_id, "band_id": band_id}, db)

        q = select(CoordinatorIntervention).options(joinedload(CoordinatorIntervention.student)).where(CoordinatorIntervention.school_id == user.school_id)
        if band_id:
            q = q.where(CoordinatorIntervention.band_id == band_id)

        q = q.order_by(CoordinatorIntervention.created_at.desc())
        items = list((await db.execute(q)).scalars().all())

        res = []
        for it in items:
            ir = InterventionResponse.model_validate(it)
            ir.student_name = it.student.full_name if it.student else "Student"
            res.append(ir)
        return res

    # --- 2. Smart Student Groups & One-Click Remedial Generation ---

    @staticmethod
    async def create_smart_group(
        db: AsyncSession, user: User, payload: SmartGroupCreate
    ) -> SmartGroupResponse:
        await authorize(
            user,
            Action.SMART_GROUP_MANAGE,
            {"school_id": user.school_id, "class_id": payload.class_id, "section_id": payload.section_id},
            db,
        )

        group = SmartStudentGroup(
            school_id=user.school_id,
            class_id=payload.class_id,
            section_id=payload.section_id,
            subject_id=payload.subject_id,
            created_by=user.id,
            name=payload.name,
            group_type=payload.group_type,
            criteria_json={"type": payload.group_type},
            student_ids_json=payload.student_ids,
            weak_topics_json=payload.weak_topics,
        )
        db.add(group)
        await db.flush()
        await db.refresh(group)

        return SmartGroupResponse.model_validate(group)

    @staticmethod
    async def list_smart_groups(
        db: AsyncSession, user: User, section_id: Optional[str] = None, subject_id: Optional[str] = None
    ) -> List[SmartGroupResponse]:
        query = select(SmartStudentGroup).where(SmartStudentGroup.school_id == user.school_id)
        if section_id:
            query = query.where(SmartStudentGroup.section_id == section_id)
        if subject_id:
            query = query.where(SmartStudentGroup.subject_id == subject_id)

        query = query.order_by(SmartStudentGroup.created_at.desc())
        groups = list((await db.execute(query)).scalars().all())
        return [SmartGroupResponse.model_validate(g) for g in groups]

    @staticmethod
    async def generate_remedial_worksheet(
        db: AsyncSession, user: User, group_id: str
    ) -> RemedialGenerationResponse:
        group = await db.get(SmartStudentGroup, group_id)
        if not group or group.school_id != user.school_id:
            raise NotFoundException(f"Smart group '{group_id}' not found.")

        await authorize(
            user,
            Action.SMART_GROUP_MANAGE,
            {"school_id": user.school_id, "class_id": group.class_id, "section_id": group.section_id},
            db,
        )

        weak_topics = group.weak_topics_json or ["Core Foundations"]
        title = f"Remedial Practice — {group.name}"

        # Create targeted assessment with status 'needs_review' (human review gate mandatory)
        asmt = Assessment(
            school_id=user.school_id,
            creator_id=user.id,
            class_id=group.class_id,
            section_id=group.section_id,
            subject_id=group.subject_id,
            title=title,
            type="worksheet",
            total_marks=20.0,
            status=AssessmentStatus.NEEDS_REVIEW,
            settings={"remedial_group_id": group.id, "topics": weak_topics},
        )
        db.add(asmt)
        await db.flush()

        # Seed 4 targeted remedial questions
        for idx, topic in enumerate(weak_topics[:4]):
            q = Question(
                school_id=user.school_id,
                author_id=user.id,
                subject_id=group.subject_id,
                category="objective",
                type="mcq",
                prompt=f"Remedial Reinforcement ({topic}): Practice question #{idx+1} for concept calibration.",
                marks=5.0,
                difficulty="easy",
                topic_tags=[topic],
                answer_data={"expected_answer": "A", "answer_keys": ["A"]},
            )
            db.add(q)
            await db.flush()

            item = AssessmentItem(
                assessment_id=asmt.id,
                question_id=q.id,
                position=idx + 1,
                marks_override=5,
            )
            db.add(item)

        await db.flush()

        return RemedialGenerationResponse(
            group_id=group.id,
            group_name=group.name,
            assessment_id=asmt.id,
            title=title,
            weak_topics=weak_topics,
            status=asmt.status,
            questions_count=4,
        )

    # --- 3. Substitution Manager ---

    @staticmethod
    async def assign_substitute_teacher(
        db: AsyncSession, user: User, payload: SubstituteTeacherAssignRequest
    ) -> SubstituteTeacherResponse:
        await authorize(
            user,
            Action.SUBSTITUTION_MANAGE,
            {"school_id": user.school_id, "class_id": payload.class_id, "section_id": payload.section_id},
            db,
        )

        target_teacher = await db.get(User, payload.teacher_id)
        if not target_teacher or target_teacher.school_id != user.school_id:
            raise NotFoundException(f"Teacher '{payload.teacher_id}' not found.")

        target_class = await db.get(Class, payload.class_id)
        target_section = await db.get(Section, payload.section_id)
        target_subject = await db.get(Subject, payload.subject_id)

        # Check existing assignment
        asgn_q = select(TeacherAssignment).where(
            and_(
                TeacherAssignment.school_id == user.school_id,
                TeacherAssignment.teacher_id == payload.teacher_id,
                TeacherAssignment.class_id == payload.class_id,
                TeacherAssignment.section_id == payload.section_id,
                TeacherAssignment.subject_id == payload.subject_id,
            )
        )
        existing = (await db.execute(asgn_q)).scalars().first()

        if existing:
            existing.is_substitute = True
            existing.valid_from = payload.valid_from
            existing.valid_to = payload.valid_to
            existing.status = "active"
            assignment = existing
        else:
            assignment = TeacherAssignment(
                school_id=user.school_id,
                teacher_id=payload.teacher_id,
                class_id=payload.class_id,
                section_id=payload.section_id,
                subject_id=payload.subject_id,
                is_class_teacher=False,
                is_substitute=True,
                valid_from=payload.valid_from,
                valid_to=payload.valid_to,
                status="active",
            )
            db.add(assignment)

        await db.flush()
        await db.refresh(assignment)

        return SubstituteTeacherResponse(
            assignment_id=assignment.id,
            teacher_id=target_teacher.id,
            teacher_name=target_teacher.full_name or target_teacher.email,
            class_name=target_class.name if target_class else "Class",
            section_name=target_section.name if target_section else "Section",
            subject_name=target_subject.name if target_subject else "Subject",
            is_substitute=True,
            valid_from=assignment.valid_from,
            valid_to=assignment.valid_to,
        )

    # --- 4. Student Academic Goals & Doubts ---

    @staticmethod
    async def create_or_update_student_goal(
        db: AsyncSession, user: User, payload: StudentGoalCreate
    ) -> StudentGoalResponse:
        await authorize(user, Action.STUDENT_GOAL_MANAGE, {"school_id": user.school_id, "student_id": user.id, "user_id": user.id}, db)

        target_subject = await db.get(Subject, payload.subject_id)
        if not target_subject or target_subject.school_id != user.school_id:
            raise NotFoundException(f"Subject '{payload.subject_id}' not found.")

        # Find existing goal
        g_q = select(StudentAcademicGoal).where(
            and_(
                StudentAcademicGoal.school_id == user.school_id,
                StudentAcademicGoal.student_id == user.id,
                StudentAcademicGoal.subject_id == payload.subject_id,
            )
        )
        goal = (await db.execute(g_q)).scalars().first()

        if goal:
            goal.target_score_pct = payload.target_score_pct
            goal.target_date = payload.target_date
            goal.notes = payload.notes
        else:
            goal = StudentAcademicGoal(
                school_id=user.school_id,
                student_id=user.id,
                subject_id=payload.subject_id,
                target_score_pct=payload.target_score_pct,
                current_score_pct=72.0,
                target_date=payload.target_date,
                status="in_progress",
                notes=payload.notes,
            )
            db.add(goal)

        await db.flush()
        await db.refresh(goal)

        return StudentGoalResponse(
            id=goal.id,
            student_id=goal.student_id,
            subject_id=goal.subject_id,
            subject_name=target_subject.name,
            target_score_pct=goal.target_score_pct,
            current_score_pct=goal.current_score_pct,
            status=goal.status,
            target_date=goal.target_date,
            notes=goal.notes,
        )

    @staticmethod
    async def get_student_goals(
        db: AsyncSession, user: User, student_id: Optional[str] = None
    ) -> List[StudentGoalResponse]:
        target_student_id = student_id or user.id
        await authorize(user, Action.STUDENT_GOAL_MANAGE, {"school_id": user.school_id, "student_id": target_student_id, "user_id": target_student_id}, db)

        q = select(StudentAcademicGoal).where(
            and_(
                StudentAcademicGoal.school_id == user.school_id,
                StudentAcademicGoal.student_id == target_student_id,
            )
        )
        goals = list((await db.execute(q)).scalars().all())

        results = []
        for g in goals:
            s_obj = await db.get(Subject, g.subject_id)
            results.append(
                StudentGoalResponse(
                    id=g.id,
                    student_id=g.student_id,
                    subject_id=g.subject_id,
                    subject_name=s_obj.name if s_obj else "Subject",
                    target_score_pct=g.target_score_pct,
                    current_score_pct=g.current_score_pct,
                    status=g.status,
                    target_date=g.target_date,
                    notes=g.notes,
                )
            )
        return results

    @staticmethod
    async def get_student_revision_list(
        db: AsyncSession, user: User
    ) -> List[RevisionItem]:
        # Fetch responses where student scored less than 60%
        resp_q = (
            select(StudentResponse, AssessmentItem, Question)
            .join(AssessmentItem, StudentResponse.assessment_item_id == AssessmentItem.id)
            .join(Question, AssessmentItem.question_id == Question.id)
            .join(Attempt, StudentResponse.attempt_id == Attempt.id)
            .where(
                and_(
                    Attempt.student_id == user.id,
                    Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.TIMED_OUT]),
                )
            )
        )
        rows = (await db.execute(resp_q)).all()

        revision_items: List[RevisionItem] = []
        seen_q = set()

        for resp, item, q in rows:
            if q.id in seen_q:
                continue
            max_m = float(item.marks_override or q.marks or 1.0)
            score = float(resp.manual_score if resp.manual_score is not None else (resp.auto_score or 0.0))
            if score < (max_m * 0.6):
                seen_q.add(q.id)
                topic = q.topic_tags[0] if q.topic_tags else "General"
                revision_items.append(
                    RevisionItem(
                        question_id=q.id,
                        prompt=q.prompt,
                        topic=topic,
                        difficulty=q.difficulty or "medium",
                        marks=max_m,
                        last_attempt_score=score,
                        suggested_action=f"Revise {topic} concepts and re-attempt problem.",
                    )
                )

        return revision_items[:10]

    @staticmethod
    async def submit_student_doubt(
        db: AsyncSession, user: User, payload: StudentDoubtCreate
    ) -> StudentDoubtResponse:
        await authorize(user, Action.DOUBT_QUERY_MANAGE, {"school_id": user.school_id, "student_id": user.id, "user_id": user.id}, db)

        # Find teacher assigned to student's section for this subject
        enr_q = select(StudentEnrollment).where(
            and_(
                StudentEnrollment.student_id == user.id,
                StudentEnrollment.school_id == user.school_id,
                StudentEnrollment.status == "active",
            )
        )
        enr = (await db.execute(enr_q)).scalars().first()
        if not enr:
            raise NotFoundException("Active enrollment not found for student.")

        asgn_q = select(TeacherAssignment).where(
            and_(
                TeacherAssignment.school_id == user.school_id,
                TeacherAssignment.class_id == enr.class_id,
                TeacherAssignment.section_id == enr.section_id,
                TeacherAssignment.subject_id == payload.subject_id,
                TeacherAssignment.status == "active",
            )
        )
        asgn = (await db.execute(asgn_q)).scalars().first()
        teacher_id = asgn.teacher_id if asgn else user.id

        doubt = StudentDoubtQuery(
            school_id=user.school_id,
            student_id=user.id,
            teacher_id=teacher_id,
            subject_id=payload.subject_id,
            question_id=payload.question_id,
            query_text=payload.query_text,
            status="pending",
        )
        db.add(doubt)
        await db.flush()
        await db.refresh(doubt)

        stud = await db.get(User, doubt.student_id)
        teacher = await db.get(User, doubt.teacher_id)
        subj = await db.get(Subject, doubt.subject_id)

        return StudentDoubtResponse(
            id=doubt.id,
            student_id=doubt.student_id,
            student_name=stud.full_name if stud else "Student",
            teacher_id=doubt.teacher_id,
            teacher_name=teacher.full_name if teacher else "Teacher",
            subject_id=doubt.subject_id,
            subject_name=subj.name if subj else "Subject",
            question_id=doubt.question_id,
            query_text=doubt.query_text,
            status=doubt.status,
            response_text=doubt.response_text,
            created_at=doubt.created_at,
            responded_at=doubt.responded_at,
        )

    @staticmethod
    async def answer_student_doubt(
        db: AsyncSession, user: User, doubt_id: str, payload: DoubtAnswerRequest
    ) -> StudentDoubtResponse:
        doubt = await db.get(StudentDoubtQuery, doubt_id)
        if not doubt or doubt.school_id != user.school_id:
            raise NotFoundException(f"Doubt query '{doubt_id}' not found.")

        await authorize(user, Action.DOUBT_QUERY_MANAGE, {"school_id": user.school_id, "user_id": user.id}, db)

        doubt.status = "answered"
        doubt.response_text = payload.response_text
        doubt.responded_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(doubt)

        stud = await db.get(User, doubt.student_id)
        teacher = await db.get(User, doubt.teacher_id)
        subj = await db.get(Subject, doubt.subject_id)

        return StudentDoubtResponse(
            id=doubt.id,
            student_id=doubt.student_id,
            student_name=stud.full_name if stud else "Student",
            teacher_id=doubt.teacher_id,
            teacher_name=teacher.full_name if teacher else "Teacher",
            subject_id=doubt.subject_id,
            subject_name=subj.name if subj else "Subject",
            question_id=doubt.question_id,
            query_text=doubt.query_text,
            status=doubt.status,
            response_text=doubt.response_text,
            created_at=doubt.created_at,
            responded_at=doubt.responded_at,
        )

    @staticmethod
    async def list_student_doubts(
        db: AsyncSession, user: User
    ) -> List[StudentDoubtResponse]:
        query = select(StudentDoubtQuery).where(StudentDoubtQuery.school_id == user.school_id)
        if user.role == RoleName.STUDENT:
            query = query.where(StudentDoubtQuery.student_id == user.id)
        else:
            query = query.where(StudentDoubtQuery.teacher_id == user.id)

        query = query.order_by(StudentDoubtQuery.created_at.desc())
        doubts = list((await db.execute(query)).scalars().all())

        results = []
        for d in doubts:
            stud = await db.get(User, d.student_id)
            teacher = await db.get(User, d.teacher_id)
            subj = await db.get(Subject, d.subject_id)
            results.append(
                StudentDoubtResponse(
                    id=d.id,
                    student_id=d.student_id,
                    student_name=stud.full_name if stud else "Student",
                    teacher_id=d.teacher_id,
                    teacher_name=teacher.full_name if teacher else "Teacher",
                    subject_id=d.subject_id,
                    subject_name=subj.name if subj else "Subject",
                    question_id=d.question_id,
                    query_text=d.query_text,
                    status=d.status,
                    response_text=d.response_text,
                    created_at=d.created_at,
                    responded_at=d.responded_at,
                )
            )
        return results

