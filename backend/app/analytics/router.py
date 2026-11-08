from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.identity.models import User, UserRole
from backend.app.analytics.schemas import (
    ClassAnalytics,
    AssessmentAnalytics,
    TopicMastery,
    TeacherDashboardSummary,
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
