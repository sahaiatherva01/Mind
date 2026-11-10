"""feat_phase7_exams_calendar_reports

Revision ID: 19657dae75f8
Revises: c61e1970b7e6
Create Date: 2026-11-10 16:28:51.523440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19657dae75f8'
down_revision: Union[str, Sequence[str], None] = 'c61e1970b7e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create calendar_events table
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', sa.String(length=36), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('band_id', sa.String(length=36), sa.ForeignKey('bands.id', ondelete='SET NULL'), nullable=True),
        sa.Column('class_id', sa.String(length=36), sa.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('section_id', sa.String(length=36), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False, server_default='event'),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_calendar_school_dates', 'calendar_events', ['school_id', 'starts_at', 'ends_at'])
    op.create_index('ix_calendar_scope', 'calendar_events', ['school_id', 'band_id', 'class_id', 'section_id'])

    # 2. Create exam_blueprints table
    op.create_table(
        'exam_blueprints',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('band_id', sa.String(length=36), sa.ForeignKey('bands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.String(length=36), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', sa.String(length=36), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('creator_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('total_marks', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='180'),
        sa.Column('term', sa.String(length=50), nullable=False, server_default='Term 1'),
        sa.Column('structure_json', sa.JSON(), nullable=False),
        sa.Column('sets_data_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('approved_by', sa.String(length=36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_blueprints_school_band', 'exam_blueprints', ['school_id', 'band_id'])
    op.create_index('ix_blueprints_status', 'exam_blueprints', ['status'])

    # 3. Add columns to attempts (batch mode for SQLite compatibility)
    with op.batch_alter_table('attempts') as batch_op:
        batch_op.add_column(sa.Column('tab_switches_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('integrity_events_json', sa.JSON(), nullable=True))

    # 4. Add columns to student_responses
    with op.batch_alter_table('student_responses') as batch_op:
        batch_op.add_column(sa.Column('ai_suggested_score', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('ai_feedback_suggestion', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('student_responses') as batch_op:
        batch_op.drop_column('ai_feedback_suggestion')
        batch_op.drop_column('ai_suggested_score')

    with op.batch_alter_table('attempts') as batch_op:
        batch_op.drop_column('integrity_events_json')
        batch_op.drop_column('tab_switches_count')

    op.drop_table('exam_blueprints')
    op.drop_table('calendar_events')
