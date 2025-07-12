"""Add business settings and team management tables

Revision ID: 3b4c2be14fe3
Revises: c68258ef0300
Create Date: 2025-07-12 09:08:44.517072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3b4c2be14fe3'
down_revision: Union[str, Sequence[str], None] = 'c68258ef0300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create business_settings table
    op.create_table('business_settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=True),
        sa.Column('company_email', sa.String(length=100), nullable=True),
        sa.Column('company_phone', sa.String(length=20), nullable=True),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=200), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('address_line_1', sa.String(length=200), nullable=True),
        sa.Column('address_line_2', sa.String(length=200), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=True, default='PT'),
        sa.Column('default_currency', sa.String(length=3), nullable=True, default='EUR'),
        sa.Column('fiscal_year_start', sa.String(length=10), nullable=True, default='01-01'),
        sa.Column('business_type', sa.String(length=50), nullable=True, default='service'),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('default_payment_terms', sa.Integer(), nullable=True, default=30),
        sa.Column('late_fee_percentage', sa.Numeric(precision=5, scale=2), nullable=True, default=0.00),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_business_settings_id', 'business_settings', ['id'], unique=False)
    op.create_index('ix_business_settings_user_id', 'business_settings', ['user_id'], unique=False)

    # Create team_members table
    op.create_table('team_members',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_owner_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('invitation_token', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=True, default='user'),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('job_title', sa.String(length=100), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_team_members_id', 'team_members', ['id'], unique=False)
    op.create_index('ix_team_members_organization_owner_id', 'team_members', ['organization_owner_id'], unique=False)
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'], unique=False)

    # Create team_invitations table
    op.create_table('team_invitations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_member_id', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['team_member_id'], ['team_members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_team_invitations_id', 'team_invitations', ['id'], unique=False)
    op.create_index('ix_team_invitations_team_member_id', 'team_invitations', ['team_member_id'], unique=False)

    # Update tax_configurations table to add new fields
    op.add_column('tax_configurations', sa.Column('description', sa.String(length=255), nullable=True))
    op.alter_column('tax_configurations', 'tax_name', new_column_name='name')
    op.alter_column('tax_configurations', 'tax_rate', new_column_name='rate')


def downgrade() -> None:
    # Remove the new fields from tax_configurations
    op.alter_column('tax_configurations', 'name', new_column_name='tax_name')
    op.alter_column('tax_configurations', 'rate', new_column_name='tax_rate')
    op.drop_column('tax_configurations', 'description')

    # Drop team_invitations table
    op.drop_index('ix_team_invitations_team_member_id', table_name='team_invitations')
    op.drop_index('ix_team_invitations_id', table_name='team_invitations')
    op.drop_table('team_invitations')

    # Drop team_members table
    op.drop_index('ix_team_members_user_id', table_name='team_members')
    op.drop_index('ix_team_members_organization_owner_id', table_name='team_members')
    op.drop_index('ix_team_members_id', table_name='team_members')
    op.drop_table('team_members')

    # Drop business_settings table
    op.drop_index('ix_business_settings_user_id', table_name='business_settings')
    op.drop_index('ix_business_settings_id', table_name='business_settings')
    op.drop_table('business_settings')
