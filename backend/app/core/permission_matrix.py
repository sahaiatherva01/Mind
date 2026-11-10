"""
Permission Matrix Contract — Mind V2
Machine-readable specification of 5-tier role and scope authorization rules.
Governs all access decisions evaluated via authorize(actor, action, resource).
"""
from typing import Dict, List, Optional, Any, Set
from backend.app.identity.models import RoleName


class Action:
    # Platform Administration
    SCHOOL_CREATE = "school.create"
    SCHOOL_UPDATE = "school.update"
    SCHOOL_SUSPEND = "school.suspend"
    SCHOOL_LIST = "school.list"
    SCHOOL_ADMIN_CREATE = "school_admin.create"
    COORDINATOR_CREATE = "coordinator.create"
    PLATFORM_DASHBOARD_VIEW = "platform.dashboard.view"
    PLATFORM_AUDIT_VIEW = "platform.audit.view"
    FEATURE_FLAG_MANAGE = "feature_flag.manage"

    # School Administration
    SCHOOL_PROFILE_UPDATE = "school.profile.update"
    BAND_MANAGE = "band.manage"
    ACADEMIC_YEAR_MANAGE = "academic_year.manage"
    CLASS_MANAGE = "class.manage"
    SECTION_MANAGE = "section.manage"
    SUBJECT_MANAGE = "subject.manage"
    STAFF_DIRECTORY_VIEW = "staff.directory.view"
    STUDENT_DIRECTORY_VIEW = "student.directory.view"
    SCHOOL_SETTINGS_MANAGE = "school.settings.manage"
    CLASS_TEACHER_DESIGNATE = "class_teacher.designate"

    # Academic Coordinator
    COORDINATOR_DASHBOARD_VIEW = "coordinator.dashboard.view"
    TEACHER_CREATE = "teacher.create"
    TEACHER_UPDATE = "teacher.update"
    TEACHER_ASSIGN = "teacher.assign"
    ROSTER_VERIFY = "roster.verify"
    ROSTER_LOCK = "roster.lock"
    ROSTER_CHANGE_APPROVE = "roster_change.approve"
    BAND_EXAM_APPROVE = "band_exam.approve"

    # Teacher / Class Teacher
    STUDENT_CREATE = "student.create"
    STUDENT_CREDENTIALS_ISSUE = "student.credentials.issue"
    ROSTER_CHANGE_REQUEST = "roster_change.request"
    MATERIALS_UPLOAD = "materials.upload"
    MATERIALS_SHARE = "materials.share"
    QUESTION_EXTRACT = "question.extract"
    ASSESSMENT_GENERATE = "assessment.generate"
    ASSESSMENT_CREATE = "assessment.create"
    ASSESSMENT_EDIT = "assessment.edit"
    ASSESSMENT_APPROVE = "assessment.approve"
    ASSESSMENT_PUBLISH = "assessment.publish"
    ASSESSMENT_SCHEDULE = "assessment.schedule"
    ASSESSMENT_EVALUATE = "assessment.evaluate"
    ASSESSMENT_RELEASE = "assessment.release_results"

    # Student
    MY_LEARNING_VIEW = "my_learning.view"
    ASSESSMENT_ATTEMPT = "assessment.attempt"
    ASSESSMENT_SUBMIT = "assessment.submit"
    RESULTS_VIEW = "results.view"
    PERFORMANCE_MAP_VIEW = "performance_map.view"

    # Analytics
    ANALYTICS_SCHOOL_VIEW = "analytics.school.view"
    ANALYTICS_BAND_VIEW = "analytics.band.view"
    ANALYTICS_TEACHER_VIEW = "analytics.teacher.view"
    ANALYTICS_STUDENT_VIEW = "analytics.student.view"

    # Audit
    AUDIT_LOG_VIEW = "audit.log.view"


# Machine-readable permissions contract
# Maps Action -> Dict of Role -> Required Scope Type
# Scope Types: 'global', 'school', 'band', 'assigned_class', 'class_teacher', 'self'
PERMISSION_MATRIX: Dict[str, Dict[str, str]] = {
    # Platform Admin Actions
    Action.SCHOOL_CREATE: {RoleName.PLATFORM_ADMIN: "global"},
    Action.SCHOOL_UPDATE: {RoleName.PLATFORM_ADMIN: "global"},
    Action.SCHOOL_SUSPEND: {RoleName.PLATFORM_ADMIN: "global"},
    Action.SCHOOL_LIST: {RoleName.PLATFORM_ADMIN: "global"},
    Action.SCHOOL_ADMIN_CREATE: {RoleName.PLATFORM_ADMIN: "global"},
    Action.COORDINATOR_CREATE: {RoleName.PLATFORM_ADMIN: "global"},
    Action.PLATFORM_DASHBOARD_VIEW: {RoleName.PLATFORM_ADMIN: "global"},
    Action.PLATFORM_AUDIT_VIEW: {RoleName.PLATFORM_ADMIN: "global"},
    Action.FEATURE_FLAG_MANAGE: {RoleName.PLATFORM_ADMIN: "global"},

    # School Admin Actions
    Action.SCHOOL_PROFILE_UPDATE: {RoleName.SCHOOL_ADMIN: "school"},
    Action.BAND_MANAGE: {RoleName.SCHOOL_ADMIN: "school"},
    Action.ACADEMIC_YEAR_MANAGE: {RoleName.SCHOOL_ADMIN: "school"},
    Action.CLASS_MANAGE: {RoleName.SCHOOL_ADMIN: "school"},
    Action.SECTION_MANAGE: {RoleName.SCHOOL_ADMIN: "school"},
    Action.SUBJECT_MANAGE: {RoleName.SCHOOL_ADMIN: "school"},
    Action.STAFF_DIRECTORY_VIEW: {RoleName.SCHOOL_ADMIN: "school", RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.STUDENT_DIRECTORY_VIEW: {RoleName.SCHOOL_ADMIN: "school", RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.SCHOOL_SETTINGS_MANAGE: {RoleName.SCHOOL_ADMIN: "school"},
    Action.CLASS_TEACHER_DESIGNATE: {RoleName.SCHOOL_ADMIN: "school", RoleName.ACADEMIC_COORDINATOR: "band"},

    # Coordinator Actions
    Action.COORDINATOR_DASHBOARD_VIEW: {RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.TEACHER_CREATE: {RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.TEACHER_UPDATE: {RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.TEACHER_ASSIGN: {RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.ROSTER_VERIFY: {RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.ROSTER_LOCK: {RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.ROSTER_CHANGE_APPROVE: {RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.BAND_EXAM_APPROVE: {RoleName.ACADEMIC_COORDINATOR: "band"},

    # Teacher Actions
    Action.STUDENT_CREATE: {RoleName.TEACHER: "class_teacher", RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.STUDENT_CREDENTIALS_ISSUE: {RoleName.TEACHER: "class_teacher", RoleName.ACADEMIC_COORDINATOR: "band"},
    Action.ROSTER_CHANGE_REQUEST: {RoleName.TEACHER: "class_teacher"},
    Action.MATERIALS_UPLOAD: {RoleName.TEACHER: "school"},
    Action.MATERIALS_SHARE: {RoleName.TEACHER: "assigned_class"},
    Action.QUESTION_EXTRACT: {RoleName.TEACHER: "school"},
    Action.ASSESSMENT_GENERATE: {RoleName.TEACHER: "assigned_class"},
    Action.ASSESSMENT_CREATE: {RoleName.TEACHER: "assigned_class"},
    Action.ASSESSMENT_EDIT: {RoleName.TEACHER: "assigned_class"},
    Action.ASSESSMENT_APPROVE: {RoleName.TEACHER: "assigned_class"},
    Action.ASSESSMENT_PUBLISH: {RoleName.TEACHER: "assigned_class"},
    Action.ASSESSMENT_SCHEDULE: {RoleName.TEACHER: "assigned_class"},
    Action.ASSESSMENT_EVALUATE: {RoleName.TEACHER: "assigned_class", RoleName.SCHOOL_ADMIN: "school"},
    Action.ASSESSMENT_RELEASE: {RoleName.TEACHER: "assigned_class"},

    # Student Actions
    Action.MY_LEARNING_VIEW: {RoleName.STUDENT: "enrolled_section"},
    Action.ASSESSMENT_ATTEMPT: {RoleName.STUDENT: "enrolled_section"},
    Action.ASSESSMENT_SUBMIT: {RoleName.STUDENT: "enrolled_section"},
    Action.RESULTS_VIEW: {RoleName.STUDENT: "self"},
    Action.PERFORMANCE_MAP_VIEW: {RoleName.STUDENT: "self"},

    # Analytics Actions
    Action.ANALYTICS_SCHOOL_VIEW: {RoleName.SCHOOL_ADMIN: "school", RoleName.PLATFORM_ADMIN: "global"},
    Action.ANALYTICS_BAND_VIEW: {RoleName.ACADEMIC_COORDINATOR: "band", RoleName.SCHOOL_ADMIN: "school"},
    Action.ANALYTICS_TEACHER_VIEW: {RoleName.TEACHER: "assigned_class", RoleName.SCHOOL_ADMIN: "school"},
    Action.ANALYTICS_STUDENT_VIEW: {RoleName.STUDENT: "self", RoleName.TEACHER: "assigned_class", RoleName.SCHOOL_ADMIN: "school"},

    # Audit Actions
    Action.AUDIT_LOG_VIEW: {RoleName.PLATFORM_ADMIN: "global", RoleName.SCHOOL_ADMIN: "school"},
}


def is_action_permitted_for_role(role: str, action: str) -> bool:
    """Checks whether a role is theoretically capable of performing an action."""
    action_rules = PERMISSION_MATRIX.get(action, {})
    return role in action_rules


def get_required_scope(role: str, action: str) -> Optional[str]:
    """Returns the scope type required for the role to perform this action."""
    action_rules = PERMISSION_MATRIX.get(action, {})
    return action_rules.get(role)
