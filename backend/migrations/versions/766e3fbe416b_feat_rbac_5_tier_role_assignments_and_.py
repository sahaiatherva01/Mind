"""feat_rbac_5_tier_role_assignments_and_bands

Revision ID: 766e3fbe416b
Revises: f0506b03ca22
Create Date: 2026-11-10 14:49:43.592404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '766e3fbe416b'
down_revision: Union[str, Sequence[str], None] = 'f0506b03ca22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to Phase 1 5-tier scoped RBAC."""
    # 1. Bands table
    op.create_table(
        'bands',
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('min_grade', sa.Integer(), nullable=False),
        sa.Column('max_grade', sa.Integer(), nullable=False),
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('school_id', 'name', name='uq_school_band_name')
    )
    op.create_index('ix_bands_school_id', 'bands', ['school_id'])

    # 2. Role Assignments table
    op.create_table(
        'role_assignments',
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=True),
        sa.Column('band_id', sa.String(length=36), sa.ForeignKey('bands.id', ondelete='SET NULL'), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_role_assignments_user_active', 'role_assignments', ['user_id', 'status'])
    op.create_index('ix_role_assignments_lookup', 'role_assignments', ['school_id', 'role', 'status'])
    op.create_index('ix_role_assignments_band', 'role_assignments', ['band_id'])

    # 3. Add columns using batch_alter_table for SQLite compatibility
    with op.batch_alter_table('schools') as batch_op:
        batch_op.add_column(sa.Column('code', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('board', sa.String(length=50), nullable=False, server_default='ICSE/ISC'))
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))

    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.alter_column('school_id', existing_type=sa.String(length=36), nullable=True)

    with op.batch_alter_table('audit_events') as batch_op:
        batch_op.alter_column('school_id', existing_type=sa.String(length=36), nullable=True)

    with op.batch_alter_table('classes') as batch_op:
        batch_op.add_column(sa.Column('band_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('grade_level', sa.Integer(), nullable=True))

    with op.batch_alter_table('teacher_assignments') as batch_op:
        batch_op.add_column(sa.Column('academic_year_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('is_class_teacher', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))

    with op.batch_alter_table('student_enrollments') as batch_op:
        batch_op.add_column(sa.Column('academic_year_id', sa.String(length=36), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('student_enrollments') as batch_op:
        batch_op.drop_column('academic_year_id')

    with op.batch_alter_table('teacher_assignments') as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('is_class_teacher')
        batch_op.drop_column('academic_year_id')

    with op.batch_alter_table('classes') as batch_op:
        batch_op.drop_column('grade_level')
        batch_op.drop_column('band_id')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('must_change_password')

    with op.batch_alter_table('schools') as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('board')
        batch_op.drop_column('code')

    op.drop_table('role_assignments')
    op.drop_table('bands')
