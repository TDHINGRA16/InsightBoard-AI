"""Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create profiles table
    op.create_table(
        'profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_profiles_email', 'profiles', ['email'])

    # Create transcripts table
    op.create_table(
        'transcripts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(10), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.Enum('uploaded', 'analyzing', 'analyzed', 'failed', name='transcriptstatus'), nullable=False),
        sa.Column('analysis_result', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash')
    )
    op.create_index('ix_transcripts_user_id', 'transcripts', ['user_id'])
    op.create_index('ix_transcripts_status', 'transcripts', ['status'])
    op.create_index('ix_transcripts_content_hash', 'transcripts', ['content_hash'])
    op.create_index('ix_transcripts_user_created', 'transcripts', ['user_id', 'created_at'])

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transcript_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='taskpriority'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'blocked', name='taskstatus'), nullable=False),
        sa.Column('assignee', sa.String(255), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('position_x', sa.Float(), nullable=True),
        sa.Column('position_y', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tasks_transcript_id', 'tasks', ['transcript_id'])
    op.create_index('ix_tasks_transcript_status', 'tasks', ['transcript_id', 'status'])
    op.create_index('ix_tasks_transcript_priority', 'tasks', ['transcript_id', 'priority'])

    # Create dependencies table
    op.create_table(
        'dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('depends_on_task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependency_type', sa.Enum('blocks', 'precedes', 'parent_of', 'related_to', name='dependencytype'), nullable=False),
        sa.Column('lag_days', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['depends_on_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('task_id != depends_on_task_id', name='check_no_self_dependency')
    )
    op.create_index('ix_dependencies_task_id', 'dependencies', ['task_id'])
    op.create_index('ix_dependencies_depends_on_task_id', 'dependencies', ['depends_on_task_id'])
    op.create_index('ix_dependencies_unique_pair', 'dependencies', ['task_id', 'depends_on_task_id'], unique=True)

    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transcript_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.Enum('analyze', 'export', 'optimize', name='jobtype'), nullable=False),
        sa.Column('status', sa.Enum('queued', 'processing', 'completed', 'failed', name='jobstatus'), nullable=False),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(100), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, default=0),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key')
    )
    op.create_index('ix_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('ix_jobs_transcript_id', 'jobs', ['transcript_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_idempotency_key', 'jobs', ['idempotency_key'])
    op.create_index('ix_jobs_user_status', 'jobs', ['user_id', 'status'])

    # Create graphs table
    op.create_table(
        'graphs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transcript_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nodes_count', sa.Integer(), nullable=False, default=0),
        sa.Column('edges_count', sa.Integer(), nullable=False, default=0),
        sa.Column('critical_path', postgresql.JSONB(), nullable=True),
        sa.Column('critical_path_length', sa.Float(), nullable=True),
        sa.Column('total_duration_days', sa.Float(), nullable=True),
        sa.Column('slack_data', postgresql.JSONB(), nullable=True),
        sa.Column('graph_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transcript_id')
    )
    op.create_index('ix_graphs_transcript_id', 'graphs', ['transcript_id'])

    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.Enum(
            'analysis.completed', 'analysis.failed', 'task.created', 
            'task.updated', 'task.completed', 'export.completed',
            name='webhookeventtype'
        ), nullable=False),
        sa.Column('endpoint_url', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('secret_key', sa.String(64), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_webhooks_user_id', 'webhooks', ['user_id'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.Enum('created', 'updated', 'deleted', name='auditaction'), nullable=False),
        sa.Column('resource_type', sa.Enum('transcript', 'task', 'dependency', 'webhook', 'job', name='resourcetype'), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=False),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_logs_user_date', 'audit_logs', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('webhooks')
    op.drop_table('graphs')
    op.drop_table('jobs')
    op.drop_table('dependencies')
    op.drop_table('tasks')
    op.drop_table('transcripts')
    op.drop_table('profiles')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS auditaction')
    op.execute('DROP TYPE IF EXISTS resourcetype')
    op.execute('DROP TYPE IF EXISTS webhookeventtype')
    op.execute('DROP TYPE IF EXISTS jobstatus')
    op.execute('DROP TYPE IF EXISTS jobtype')
    op.execute('DROP TYPE IF EXISTS dependencytype')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS taskpriority')
    op.execute('DROP TYPE IF EXISTS transcriptstatus')
