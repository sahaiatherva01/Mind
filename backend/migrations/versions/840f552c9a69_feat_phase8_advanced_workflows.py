"""feat_phase8_advanced_workflows

Revision ID: 840f552c9a69
Revises: 19657dae75f8
Create Date: 2026-11-10 17:02:14.391280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '840f552c9a69'
down_revision: Union[str, Sequence[str], None] = '19657dae75f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update teacher_assignments with substitution temporal fields
    with op.batch_alter_table('teacher_assignments') as batch_op:
        batch_op.add_column(sa.Column('is_substitute', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True))

    # 2. Create coordinator_interventions table
    op.create_table(
        'coordinator_interventions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('band_id', sa.String(length=36), sa.ForeignKey('bands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('trigger_reason', sa.String(length=500), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('action_taken', sa.String(length=1000), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_interventions_school_band', 'coordinator_interventions', ['school_id', 'band_id'])
    op.create_index('ix_interventions_student', 'coordinator_interventions', ['student_id'])
    op.create_index('ix_interventions_status', 'coordinator_interventions', ['status'])

    # 3. Create smart_student_groups table
    op.create_table(
        'smart_student_groups',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', sa.String(length=36), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', sa.String(length=36), sa.ForeignKey('sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('group_type', sa.String(length=50), nullable=False, server_default='remedial'),
        sa.Column('criteria_json', sa.JSON(), nullable=False),
        sa.Column('student_ids_json', sa.JSON(), nullable=False),
        sa.Column('weak_topics_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_smart_groups_scope', 'smart_student_groups', ['school_id', 'class_id', 'section_id', 'subject_id'])

    # 4. Create student_academic_goals table
    op.create_table(
        'student_academic_goals',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_score_pct', sa.Float(), nullable=False),
        sa.Column('current_score_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='in_progress'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_student_goals', 'student_academic_goals', ['school_id', 'student_id', 'subject_id'])

    # 5. Create student_doubt_queries table
    op.create_table(
        'student_doubt_queries',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.String(length=36), sa.ForeignKey('questions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_doubt_queries_student', 'student_doubt_queries', ['school_id', 'student_id'])
    op.create_index('ix_doubt_queries_teacher', 'student_doubt_queries', ['school_id', 'teacher_id', 'status'])


def downgrade() -> None:
    op.drop_table('student_doubt_queries')
    op.drop_table('student_academic_goals')
    op.drop_table('smart_student_groups')
    op.drop_table('coordinator_interventions')

    with op.batch_alter_table('teacher_assignments') as batch_op:
        batch_op.drop_column('valid_to')
        batch_op.drop_column('valid_from')
        batch_op.drop_column('is_substitute')
