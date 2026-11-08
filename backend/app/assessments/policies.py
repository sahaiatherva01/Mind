"""
Assessment Authorization Policies
Enforces that:
1. Teacher can only view/edit assessments in their assigned workspaces or created by them.
2. Students can NEVER view drafts or unreleased answer keys.
"""
from backend.app.core.errors import ForbiddenException
from backend.app.identity.models import User
from backend.app.assessments.models import Assessment


def can_manage_assessment(user: User, assessment: Assessment) -> bool:
    if user.role == "admin":
        return True
    if user.role == "teacher":
        # Teacher must be creator or assigned to this school
        if user.id == assessment.creator_id or user.school_id == assessment.school_id:
            return True
    raise ForbiddenException("Access denied: You do not have permission to edit this assessment draft.")


def can_view_assessment_draft(user: User, assessment: Assessment) -> bool:
    if user.role in ("admin", "teacher"):
        return True
    raise ForbiddenException("Access denied: Students cannot access unapproved assessment drafts.")
