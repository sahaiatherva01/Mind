from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.identity.models import User, UserRole, RoleName
from backend.app.analytics.schemas import (
    ClassAnalytics,
    AssessmentAnalytics,
    TopicMastery,
    TeacherDashboardSummary,
    SchoolAnalyticsSummary,
    BandAnalyticsSummary,
    IndividualStudentAnalytics,
    TeacherFourLevelAnalytics,
    StudentPerformanceMap,
    AnalyticsInsightRequest,
    AnalyticsInsightResponse,
)
from backend.app.analytics.service import AnalyticsService

router = APIRouter(tags=["Analytics"])


@router.get("/analytics/classes/{class_id}", response_model=ClassAnalytics)
async def get_class_analytics(
    class_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER])),
):
    """Retrieve class-level completion and score trends."""
    return await AnalyticsService.get_class_analytics(db, current_user, class_id)


@router.get("/analytics/assessments/{assessment_id}", response_model=AssessmentAnalytics)
async def get_assessment_analytics(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER])),
):
    """Retrieve assessment question-wise item analysis and discrimination indices."""
    return await AnalyticsService.get_assessment_analytics(db, current_user, assessment_id)


@router.get("/analytics/topics", response_model=List[TopicMastery])
async def get_topic_analytics(
    subject_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER])),
):
    """Retrieve topic mastery and learning gap trends for authorised scope."""
    return await AnalyticsService.get_topic_analytics(db, current_user, subject_id)


@router.get("/teacher/dashboard-summary", response_model=TeacherDashboardSummary)
async def get_teacher_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
):
    """Summary counts for teacher dashboard: assigned classes, pending evaluations, etc."""
    return await AnalyticsService.get_teacher_dashboard_summary(db, current_user)


# --- Phase 6: Scoped Multi-Level Analytics Endpoints ---

@router.get("/analytics/school", response_model=SchoolAnalyticsSummary)
async def get_school_analytics(
    school_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve school-wide academic indicators, trends, grade distribution and teacher activity."""
    return await AnalyticsService.get_school_analytics_summary(db, current_user, school_id)


@router.get("/coordinator/analytics", response_model=BandAnalyticsSummary)
async def get_coordinator_band_analytics(
    band_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve band-scoped cross-section comparisons and at-risk metrics for coordinator."""
    return await AnalyticsService.get_coordinator_band_analytics(db, current_user, band_id)


@router.get("/teacher/analytics", response_model=TeacherFourLevelAnalytics)
async def get_teacher_four_level_analytics(
    class_id: Optional[str] = None,
    section_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    student_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve 4-level analytics (Level 1: Student, Level 2: Section, Level 3: Subject, Level 4: Cross & Engagement)."""
    return await AnalyticsService.get_teacher_four_level_analytics(
        db, current_user, class_id, section_id, subject_id, student_id
    )


@router.get("/student/performance-map", response_model=StudentPerformanceMap)
async def get_student_performance_map(
    student_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve private topic mastery and learning materials progress for student."""
    return await AnalyticsService.get_student_performance_map(db, current_user, student_id)


@router.post("/analytics/insights", response_model=AnalyticsInsightResponse)
async def generate_analytics_insights(
    req: AnalyticsInsightRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analytics Insight Agent (Track A5): strictly zero text-to-SQL diagnostic synthesis."""
    return await AnalyticsService.generate_insights(db, current_user, req)
