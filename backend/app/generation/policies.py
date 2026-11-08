"""
Generation Authorization Policies
Enforces that a teacher can ONLY generate assessments for assigned Class + Section + Subject combinations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.policies import can_teacher_access_class
from backend.app.identity.models import User


async def can_generate_for_workspace(
    db: AsyncSession,
    user: User,
    class_id: str,
    section_id: str,
    subject_id: str,
) -> bool:
    await can_teacher_access_class(
        db=db,
        user=user,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
    )
    return True

