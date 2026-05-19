"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-05-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(64), nullable=False),
        sa.Column('account', sa.String(64), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False),
        sa.Column('department', sa.String(128), nullable=True),
        sa.Column('status', sa.Enum('enabled', 'disabled', name='userstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(6), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(6), nullable=True),
        sa.Index('idx_users_role', 'role'),
        sa.Index('idx_users_status', 'status'),
    )

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('target', sa.Text, nullable=False),
        sa.Column('target_normalized', sa.String(512), nullable=True),
        sa.Column('scan_mode', sa.Enum('quick', 'standard', 'deep', name='scanmode'), nullable=False),
        sa.Column('interactive', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('instruction', sa.Text, nullable=True),
        sa.Column('status', sa.Enum('not_started', 'running', 'completed', 'failed', 'stopped', name='taskstatus'), nullable=False),
        sa.Column('risk_level', sa.Enum('unknown', 'none', 'low', 'medium', 'high', name='risklevel'), nullable=False),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(6), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(6), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.Index('idx_tasks_created_by', 'created_by'),
        sa.Index('idx_tasks_status', 'status'),
        sa.Index('idx_tasks_risk_level', 'risk_level'),
        sa.Index('idx_tasks_created_at', 'created_at'),
        sa.Index('idx_tasks_deleted_at', 'deleted_at'),
        sa.Index('idx_tasks_target_normalized', 'target_normalized'),
    )

    # Create task_runs table
    op.create_table(
        'task_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), nullable=False),
        sa.Column('run_no', sa.Integer, nullable=False),
        sa.Column('scan_mode', sa.Enum('quick', 'standard', 'deep', name='scanmode'), nullable=False),
        sa.Column('interactive', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('status', sa.Enum('queued', 'running', 'stopping', 'completed', 'failed', 'stopped', name='runstatus'), nullable=False),
        sa.Column('pid', sa.Integer, nullable=True),
        sa.Column('runner_node_id', sa.String(128), nullable=True),
        sa.Column('exit_code', sa.Integer, nullable=True),
        sa.Column('run_dir', sa.String(1024), nullable=False),
        sa.Column('strix_run_dir', sa.String(1024), nullable=True),
        sa.Column('started_at', sa.DateTime(6), nullable=True),
        sa.Column('ended_at', sa.DateTime(6), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(6), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('task_id', 'run_no', name='uq_task_runs_task_run_no'),
        sa.Index('idx_task_runs_task_id', 'task_id'),
        sa.Index('idx_task_runs_status', 'status'),
        sa.Index('idx_task_runs_created_at', 'created_at'),
        sa.Index('idx_task_runs_started_at', 'started_at'),
    )

    # Create run_events table
    op.create_table(
        'run_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), nullable=False),
        sa.Column('seq', sa.BigInteger, nullable=False),
        sa.Column('event_type', sa.String(128), nullable=False),
        sa.Column('event_time', sa.DateTime(6), nullable=True),
        sa.Column('payload_json', sa.JSON, nullable=False),
        sa.Column('source_file', sa.String(1024), nullable=True),
        sa.Column('source_offset', sa.BigInteger, nullable=True),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['run_id'], ['task_runs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('run_id', 'seq', name='uq_run_events_run_seq'),
        sa.Index('idx_run_events_run_seq', 'run_id', 'seq'),
        sa.Index('idx_run_events_type', 'event_type'),
        sa.Index('idx_run_events_created_at', 'created_at'),
    )

    # Create results table
    op.create_table(
        'results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), nullable=False),
        sa.Column('run_id', sa.String(36), nullable=False),
        sa.Column('project_name', sa.String(128), nullable=False),
        sa.Column('target', sa.Text, nullable=False),
        sa.Column('scan_mode', sa.Enum('quick', 'standard', 'deep', name='scanmode'), nullable=False),
        sa.Column('interactive', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('status', sa.Enum('completed', 'failed', 'stopped', 'parse_failed', name='resultstatus'), nullable=False),
        sa.Column('risk_level', sa.Enum('unknown', 'none', 'low', 'medium', 'high', name='risklevel'), nullable=False),
        sa.Column('vulnerability_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('artifact_dir', sa.String(1024), nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('parse_error', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime(6), nullable=True),
        sa.Column('ended_at', sa.DateTime(6), nullable=True),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(6), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['run_id'], ['task_runs.id']),
        sa.UniqueConstraint('run_id', name='uq_results_run_id'),
        sa.Index('idx_results_task_id', 'task_id'),
        sa.Index('idx_results_status', 'status'),
        sa.Index('idx_results_risk_level', 'risk_level'),
        sa.Index('idx_results_started_at', 'started_at'),
    )

    # Create artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), nullable=False),
        sa.Column('result_id', sa.String(36), nullable=True),
        sa.Column('vulnerability_id', sa.String(36), nullable=True),
        sa.Column('artifact_type', sa.Enum('events_jsonl', 'markdown', 'terminal_raw', 'runner_log', 'report', 'other', name='artifacttype'), nullable=False),
        sa.Column('relative_path', sa.String(1024), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('content_type', sa.String(128), nullable=True),
        sa.Column('size_bytes', sa.BigInteger, nullable=True),
        sa.Column('sha256', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['run_id'], ['task_runs.id'], ondelete='CASCADE'),
        sa.Index('idx_artifacts_run_id', 'run_id'),
        sa.Index('idx_artifacts_result_id', 'result_id'),
        sa.Index('idx_artifacts_vuln_id', 'vulnerability_id'),
        sa.Index('idx_artifacts_type', 'artifact_type'),
    )

    # Create vulnerabilities table (after artifacts for foreign key)
    op.create_table(
        'vulnerabilities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('result_id', sa.String(36), nullable=False),
        sa.Column('ordinal', sa.Integer, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('severity', sa.Enum('unknown', 'none', 'low', 'medium', 'high', name='vulnerabilityseverity'), nullable=False),
        sa.Column('vuln_type', sa.String(128), nullable=True),
        sa.Column('affected_target', sa.Text, nullable=True),
        sa.Column('verified', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('markdown_artifact_id', sa.String(36), nullable=True),
        sa.Column('raw_json', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(6), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['result_id'], ['results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['markdown_artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('result_id', 'ordinal', name='uq_vulns_result_ordinal'),
        sa.Index('idx_vulns_result_id', 'result_id'),
        sa.Index('idx_vulns_severity', 'severity'),
        sa.Index('idx_vulns_verified', 'verified'),
    )

    # Create whitelists table
    op.create_table(
        'whitelists',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('target_type', sa.Enum('url', 'domain', 'ip', 'repo', name='whitelisttype'), nullable=False),
        sa.Column('target_value', sa.Text, nullable=False),
        sa.Column('target_normalized', sa.String(512), nullable=False),
        sa.Column('project', sa.String(128), nullable=True),
        sa.Column('status', sa.Enum('enabled', 'disabled', name='whiteliststatus'), nullable=False),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(6), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.Index('idx_whitelists_type', 'target_type'),
        sa.Index('idx_whitelists_status', 'status'),
        sa.Index('idx_whitelists_target_normalized', 'target_normalized'),
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('actor_id', sa.String(36), nullable=True),
        sa.Column('actor_account', sa.String(64), nullable=True),
        sa.Column('actor_role', sa.String(32), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('object_type', sa.String(64), nullable=True),
        sa.Column('object_id', sa.String(36), nullable=True),
        sa.Column('request_ip', sa.String(64), nullable=True),
        sa.Column('result', sa.Enum('success', 'failed', name='auditresult'), nullable=False),
        sa.Column('remark', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(6), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_audit_logs_actor_id', 'actor_id'),
        sa.Index('idx_audit_logs_action', 'action'),
        sa.Index('idx_audit_logs_result', 'result'),
        sa.Index('idx_audit_logs_created_at', 'created_at'),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('whitelists')
    op.drop_table('vulnerabilities')
    op.drop_table('artifacts')
    op.drop_table('results')
    op.drop_table('run_events')
    op.drop_table('task_runs')
    op.drop_table('tasks')
    op.drop_table('users')
