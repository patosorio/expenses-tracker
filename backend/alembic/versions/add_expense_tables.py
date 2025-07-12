"""Add expense management tables

Revision ID: add_expense_tables
Revises: add_categories
Create Date: 2025-07-11 10:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_expense_tables'
down_revision: Union[str, Sequence[str], None] = 'add_categories'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add expense management tables."""
    
    # Note: SQLAlchemy will automatically create enum types when creating tables
    # No need to manually create them as it causes conflicts
    
    # Create tax_configurations table
    op.create_table(
        'tax_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), index=True),
        sa.Column('tax_name', sa.String(100), nullable=False),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('tax_code', sa.String(20), nullable=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('country_code', sa.String(2), nullable=True),
        sa.Column('user_id', sa.String, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean, default=True),
        
        # Constraints
        sa.CheckConstraint('tax_rate >= 0 AND tax_rate <= 100', name='ck_tax_rate_range'),
        sa.UniqueConstraint('user_id', 'is_default', name='uq_default_tax_per_user'),
        sa.UniqueConstraint('user_id', 'tax_name', name='uq_tax_name_per_user'),
    )
    
    # Create indexes for tax_configurations
    op.create_index('ix_tax_configs_user_active', 'tax_configurations', ['user_id', 'is_active'])
    op.create_index('ix_tax_configs_user_default', 'tax_configurations', ['user_id', 'is_default'])
    
    # Create expenses table
    op.create_table(
        'expenses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), index=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('expense_date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('receipt_url', sa.String(500), nullable=True),
        sa.Column('expense_type', sa.Enum('simple', 'invoice', name='expensetype'), nullable=False, default='simple'),
        sa.Column('user_id', sa.String, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('payment_method', sa.Enum('cash', 'card', 'bank_transfer', 'digital_wallet', name='paymentmethod'), nullable=True),
        sa.Column('payment_status', sa.Enum('pending', 'paid', 'refunded', name='paymentstatus'), nullable=False, default='pending'),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('supplier_name', sa.String(200), nullable=True),
        sa.Column('supplier_tax_id', sa.String(50), nullable=True),
        sa.Column('payment_due_date', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('base_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='EUR'),
        sa.Column('tax_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tax_configurations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('tags', postgresql.JSON, nullable=True),
        sa.Column('custom_fields', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean, default=True),
        
        # Constraints
        sa.CheckConstraint('base_amount > 0', name='ck_expense_base_amount_positive'),
        sa.CheckConstraint('tax_amount >= 0', name='ck_expense_tax_amount_non_negative'),
        sa.CheckConstraint('total_amount > 0', name='ck_expense_total_amount_positive'),
        sa.CheckConstraint("expense_type = 'simple' OR (expense_type = 'invoice' AND supplier_name IS NOT NULL)", name='ck_expense_invoice_requires_supplier'),
        sa.CheckConstraint("payment_date IS NULL OR payment_date >= expense_date", name='ck_expense_payment_after_expense_date'),
        sa.CheckConstraint("expense_date <= CURRENT_DATE", name='ck_expense_date_not_future'),
        sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name='ck_expense_currency_format'),
    )
    
    # Create indexes for expenses
    op.create_index('ix_expenses_user_date', 'expenses', ['user_id', 'expense_date'])
    op.create_index('ix_expenses_user_category', 'expenses', ['user_id', 'category_id'])
    op.create_index('ix_expenses_user_type', 'expenses', ['user_id', 'expense_type'])
    op.create_index('ix_expenses_user_status', 'expenses', ['user_id', 'payment_status'])
    op.create_index('ix_expenses_overdue', 'expenses', ['user_id', 'payment_due_date', 'payment_status'])
    op.create_index('ix_expenses_user_active', 'expenses', ['user_id', 'is_active'])
    
    # Create document_analyses table
    op.create_table(
        'document_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), index=True),
        sa.Column('expense_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('expenses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('user_id', sa.String, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('analysis_status', sa.Enum('pending', 'processing', 'completed', 'failed', name='analysisstatus'), nullable=False, default='pending'),
        sa.Column('extracted_data', postgresql.JSON, nullable=True),
        sa.Column('confidence_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('needs_review', sa.Boolean, default=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)', name='ck_analysis_confidence_range'),
    )
    
    # Create indexes for document_analyses
    op.create_index('ix_document_analyses_user_status', 'document_analyses', ['user_id', 'analysis_status'])
    op.create_index('ix_document_analyses_user_created', 'document_analyses', ['user_id', 'created_at'])
    
    # Create expense_attachments table
    op.create_table(
        'expense_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), index=True),
        sa.Column('expense_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('expenses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.Numeric(12, 0), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('file_size > 0 AND file_size <= 52428800', name='ck_attachment_file_size'),
    )
    
    # Create indexes for expense_attachments
    op.create_index('ix_attachments_expense', 'expense_attachments', ['expense_id'])


def downgrade() -> None:
    """Downgrade schema to remove expense management tables."""
    
    # Drop tables in reverse order due to foreign key dependencies
    # SQLAlchemy will automatically drop the enum types when tables are dropped
    op.drop_table('expense_attachments')
    op.drop_table('document_analyses') 
    op.drop_table('expenses')
    op.drop_table('tax_configurations') 