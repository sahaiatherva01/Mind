"""
Assessment Authorization Policies — Mind V2
"""
from backend.app.core.errors import ForbiddenException
from backend.app.identity.models import User, RoleName
from backend.app.assessments.models import Assessment


def can_manage_assessment(user: User, assessment: Assessment) -> bool:
    roles = {r.role for r in user.role_assignments if r.status == "active"}
    if RoleName.PLATFORM_ADMIN in roles or RoleName.SCHOOL_ADMIN in roles:
        return True
    if RoleName.TEACHER in roles:
        if user.id == assessment.creator_id or user.school_id == assessment.school_id:
            return True
    raise ForbiddenException("Access denied: You do not have permission to edit this assessment draft.")


def can_view_assessment_draft(user: User, assessment: Assessment) -> bool:
    roles = {r.role for r in user.role_assignments if r.status == "active"}
    if roles.intersection({RoleName.PLATFORM_ADMIN, RoleName.SCHOOL_ADMIN, RoleName.ACADEMIC_COORDINATOR, RoleName.TEACHER}):
        return True
    raise ForbiddenException("Access denied: Students cannot access unapproved assessment drafts.")
