"""
Analytics Insight Agent — Mind V2 (Agent Track A5)
Non-negotiable architectural invariant: Strictly zero text-to-SQL.
Uses scoped, typed tool functions to retrieve deterministic diagnostic evidence
and synthesizes honest pedagogical insights.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.assessments.models import Assessment, Attempt, StudentResponse, AssessmentItem
from backend.app.content.models import Material, MaterialEngagement, Question
from backend.app.academics.models import Class, Section, Subject, StudentEnrollment
from backend.app.analytics.schemas import AnalyticsInsightResponse


class ScopedAnalyticsTools:
    """
    Typed, scoped data retrieval tools for the Analytics Insight Agent.
    Strictly zero text-to-SQL; each query is deterministic and tenant-bounded.
    """

    @staticmethod
    async def get_performance_summary(
        db: AsyncSession,
        school_id: str,
        scope_type: str,
        scope_id: Optional[str],
    ) -> Dict[str, Any]:
        """Calculates attempts count, average score, and pass rate for given scope."""
        stmt = (
            select(
                func.count(Attempt.id).label("total_attempts"),
                func.avg(Attempt.total_score).label("avg_score"),
                func.avg(Attempt.max_score).label("avg_max"),
            )
            .join(Assessment, Attempt.assessment_id == Assessment.id)
            .where(
                Attempt.school_id == school_id,
                Attempt.status == "submitted",
            )
        )

        if scope_type == "class" and scope_id:
            stmt = stmt.where(Assessment.class_id == scope_id)
        elif scope_type == "subject" and scope_id:
            stmt = stmt.where(Assessment.subject_id == scope_id)
        elif scope_type == "student" and scope_id:
            stmt = stmt.where(Attempt.student_id == scope_id)

        res = await db.execute(stmt)
        row = res.one_or_none()
        total_attempts = row.total_attempts if row else 0
        avg_score = row.avg_score if row and row.avg_score is not None else 0.0
        avg_max = row.avg_max if row and row.avg_max is not None and row.avg_max > 0 else 1.0

        avg_pct = round((avg_score / avg_max) * 100, 1) if avg_max > 0 else 0.0
        return {
            "total_attempts": total_attempts,
            "average_score_pct": avg_pct,
            "sample_size": total_attempts,
        }

    @staticmethod
    async def get_topic_gaps(
        db: AsyncSession,
        school_id: str,
        scope_type: str,
        scope_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Identifies mastery percentage by topic/chapter to surface pedagogical gaps."""
        stmt = (
            select(
                Assessment.title,
                Assessment.settings,
                func.avg(Attempt.total_score).label("avg_score"),
                func.avg(Attempt.max_score).label("avg_max"),
            )
            .join(Attempt, Assessment.id == Attempt.assessment_id)
            .where(
                Assessment.school_id == school_id,
                Attempt.status == "submitted",
            )
            .group_by(Assessment.id)
        )

        if scope_type == "class" and scope_id:
            stmt = stmt.where(Assessment.class_id == scope_id)
        elif scope_type == "subject" and scope_id:
            stmt = stmt.where(Assessment.subject_id == scope_id)
        elif scope_type == "student" and scope_id:
            stmt = stmt.where(Attempt.student_id == scope_id)

        res = await db.execute(stmt)
        rows = res.all()

        topic_data = []
        for title, settings_dict, avg_s, avg_m in rows:
            max_s = avg_m or 1.0
            score = avg_s or 0.0
            pct = round((score / max_s) * 100, 1)

            # Extract topic name from settings or assessment title
            topics = (settings_dict or {}).get("topics") or []
            topic_label = topics[0] if topics else title.split(":")[-1].strip()

            status = "mastered" if pct >= 75 else ("proficient" if pct >= 60 else "needs_reinforcement")
            topic_data.append({
                "topic": topic_label,
                "mastery_pct": pct,
                "status": status,
            })

        return topic_data

    @staticmethod
    async def get_engagement_metrics(
        db: AsyncSession,
        school_id: str,
        scope_type: str,
        scope_id: Optional[str],
    ) -> Dict[str, Any]:
        """Calculates material reading completions and engagement duration."""
        stmt = (
            select(
                func.count(MaterialEngagement.id).label("total_opens"),
                func.avg(MaterialEngagement.duration_seconds).label("avg_duration"),
                func.count(func.distinct(MaterialEngagement.material_id)).label("distinct_materials"),
            )
            .where(MaterialEngagement.school_id == school_id)
        )

        if scope_type == "student" and scope_id:
            stmt = stmt.where(MaterialEngagement.student_id == scope_id)

        res = await db.execute(stmt)
        row = res.one_or_none()
        total_opens = row.total_opens if row else 0
        avg_dur = row.avg_duration if row and row.avg_duration is not None else 0.0
        distinct_mats = row.distinct_materials if row else 0

        return {
            "total_material_opens": total_opens,
            "average_duration_minutes": round(avg_dur / 60.0, 1),
            "distinct_materials_accessed": distinct_mats,
        }


class AnalyticsInsightAgent:
    """
    Synthesizes pedagogical diagnosis by executing strictly scoped tool functions.
    Zero text-to-SQL adherence guarantees multi-tenant security and determinism.
    """

    @staticmethod
    async def generate_insights(
        db: AsyncSession,
        school_id: str,
        scope_type: str,
        scope_id: Optional[str] = None,
    ) -> AnalyticsInsightResponse:
        tools = ScopedAnalyticsTools()
        evidence_tools = ["get_performance_summary", "get_topic_gaps", "get_engagement_metrics"]

        # 1. Execute scoped data tools
        perf = await tools.get_performance_summary(db, school_id, scope_type, scope_id)
        topics = await tools.get_topic_gaps(db, school_id, scope_type, scope_id)
        engagement = await tools.get_engagement_metrics(db, school_id, scope_type, scope_id)

        # 2. Extract strengths and gaps
        strengths: List[str] = []
        gaps: List[str] = []

        for t in topics:
            if t["mastery_pct"] >= 70.0:
                strengths.append(f"Strong concept grasp in '{t['topic']}' ({t['mastery_pct']}% accuracy).")
            elif t["mastery_pct"] < 60.0:
                gaps.append(f"Conceptual weakness identified in '{t['topic']}' ({t['mastery_pct']}% accuracy).")

        if not strengths:
            strengths.append("Foundational understanding established across preliminary assessments.")
        if not gaps:
            gaps.append("No critical conceptual gaps below 60% mastery detected in recent evaluations.")

        # 3. Formulate pedagogical recommendations
        recommendations: List[str] = []
        if any(t["mastery_pct"] < 60.0 for t in topics):
            weak_topics = [t["topic"] for t in topics if t["mastery_pct"] < 60.0]
            recommendations.append(
                f"Deploy targeted remedial worksheet focusing on: {', '.join(weak_topics[:3])}."
            )

        if engagement["total_material_opens"] == 0:
            recommendations.append(
                "Increase distribution and review of foundational reading handouts before upcoming tests."
            )
        else:
            recommendations.append(
                f"Maintain structured reading pace (current average reading time: {engagement['average_duration_minutes']} min/session)."
            )

        recommendations.append("Conduct a timed formative quiz to calibrate retention prior to term examination.")

        # 4. Formulate overall diagnostic summary
        avg_score = perf["average_score_pct"]
        summary = (
            f"Academic evaluation across {perf['total_attempts']} assessed attempt(s) reveals an aggregate performance "
            f"of {avg_score}%. {len(strengths)} area(s) demonstrate solid mastery, while {len(gaps)} require "
            f"structured pedagogical reinforcement."
        )

        return AnalyticsInsightResponse(
            scope_type=scope_type,
            scope_id=scope_id,
            summary=summary,
            strengths=strengths,
            conceptual_gaps=gaps,
            pedagogical_recommendations=recommendations,
            evidence_tools_used=evidence_tools,
        )
