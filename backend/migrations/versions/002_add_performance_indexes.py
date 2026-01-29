"""Add performance indexes for N+1 query fixes.

Revision ID: 002_add_performance_indexes
Revises: 001_initial
Create Date: 2025-01-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_performance_indexes'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Task indexes
    op.create_index('idx_tasks_transcript_id', 'tasks', ['transcript_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_priority', 'tasks', ['priority'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])
    op.create_index('idx_tasks_transcript_status', 'tasks', ['transcript_id', 'status'])
    
    # Dependency indexes
    op.create_index('idx_dependencies_task_id', 'dependencies', ['task_id'])
    op.create_index('idx_dependencies_depends_on_task_id', 'dependencies', ['depends_on_task_id'])
    op.create_index('idx_dependencies_tasks', 'dependencies', ['task_id', 'depends_on_task_id'])
    
    # Transcript indexes
    op.create_index('idx_transcripts_user_id', 'transcripts', ['user_id'])
    op.create_index('idx_transcripts_status', 'transcripts', ['status'])
    op.create_index('idx_transcripts_created_at', 'transcripts', ['created_at'])


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index('idx_transcripts_created_at', table_name='transcripts')
    op.drop_index('idx_transcripts_status', table_name='transcripts')
    op.drop_index('idx_transcripts_user_id', table_name='transcripts')
    
    op.drop_index('idx_dependencies_tasks', table_name='dependencies')
    op.drop_index('idx_dependencies_depends_on_task_id', table_name='dependencies')
    op.drop_index('idx_dependencies_task_id', table_name='dependencies')
    
    op.drop_index('idx_tasks_transcript_status', table_name='tasks')
    op.drop_index('idx_tasks_created_at', table_name='tasks')
    op.drop_index('idx_tasks_priority', table_name='tasks')
    op.drop_index('idx_tasks_status', table_name='tasks')
    op.drop_index('idx_tasks_transcript_id', table_name='tasks')
