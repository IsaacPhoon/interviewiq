"""
initial migration

Revision ID: a3c5725b8b06
Revises:
Create Date: 2025-12-23 21:46:28.466490
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3c5725b8b06'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clerk_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    )
    op.create_index(op.f('ix_users_clerk_id'), 'users', ['clerk_id'], unique=True)
    op.create_table(
        'job_descriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('job_title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description_text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'QUESTIONS_GENERATED', 'ERROR', name='statusenum'),
            nullable=False,
        ),
        sa.Column('error_message', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name=op.f('fk_job_descriptions_user_id_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_job_descriptions')),
    )
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('job_description_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['job_description_id'],
            ['job_descriptions.id'],
            name=op.f('fk_questions_job_description_id_job_descriptions'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_questions')),
    )
    op.create_table(
        'responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audio_path', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('transcript', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('evaluation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['question_id'],
            ['questions.id'],
            name=op.f('fk_responses_question_id_questions'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_responses')),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('responses')
    op.drop_table('questions')
    op.drop_table('job_descriptions')
    op.drop_index(op.f('ix_users_clerk_id'), table_name='users')
    op.drop_table('users')
