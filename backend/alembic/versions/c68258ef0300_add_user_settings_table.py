"""Add user_settings table

Revision ID: c68258ef0300
Revises: add_expense_tables
Create Date: 2025-07-11 16:38:09.967503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c68258ef0300'
down_revision: Union[str, Sequence[str], None] = 'add_expense_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user_settings table."""
    op.create_table('user_settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True, default='EUR'),
        sa.Column('date_format', sa.String(length=20), nullable=True, default='DD/MM/YYYY'),
        sa.Column('time_format', sa.String(length=10), nullable=True, default='24h'),
        sa.Column('week_start', sa.String(length=10), nullable=True, default='monday'),
        sa.Column('theme', sa.String(length=10), nullable=True, default='system'),
        sa.Column('fiscal_year_start', sa.String(length=10), nullable=True, default='01-01'),
        sa.Column('email_notifications', sa.Boolean(), nullable=True, default=True),
        sa.Column('push_notifications', sa.Boolean(), nullable=True, default=True),
        sa.Column('bill_reminders', sa.Boolean(), nullable=True, default=True),
        sa.Column('weekly_reports', sa.Boolean(), nullable=True, default=False),
        sa.Column('overdue_invoices', sa.Boolean(), nullable=True, default=True),
        sa.Column('team_updates', sa.Boolean(), nullable=True, default=True),
        sa.Column('marketing_emails', sa.Boolean(), nullable=True, default=False),
        sa.Column('expense_summaries', sa.Boolean(), nullable=True, default=True),
        sa.Column('budget_alerts', sa.Boolean(), nullable=True, default=True),
        sa.Column('default_export_format', sa.String(length=10), nullable=True, default='csv'),
        sa.Column('include_attachments', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_user_settings_id', 'user_settings', ['id'], unique=False)
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'], unique=False)


def downgrade() -> None:
    """Remove user_settings table."""
    op.drop_index('ix_user_settings_user_id', table_name='user_settings')
    op.drop_index('ix_user_settings_id', table_name='user_settings')
    op.drop_table('user_settings')
