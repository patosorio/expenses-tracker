"""Add contacts table and update expenses

Revision ID: 7f8c9d4e5b2a
Revises: 3b4c2be14fe3
Create Date: 2024-01-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7f8c9d4e5b2a'
down_revision: Union[str, None] = '3b4c2be14fe3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contacts table with string-based contact_type
    op.create_table('contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('contact_type', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state_province', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=False, server_default='PT'),
        sa.Column('tax_number', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('custom_fields', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='ck_contact_email_format'),
        sa.CheckConstraint("country ~ '^[A-Z]{2}$'", name='ck_contact_country_format'),
        sa.CheckConstraint("contact_type IN ('CLIENT', 'VENDOR', 'SUPPLIER')", name='ck_contact_type_valid')
    )
    
    # Create indexes for contacts
    op.create_index('ix_contacts_id', 'contacts', ['id'])
    op.create_index('ix_contacts_contact_type', 'contacts', ['contact_type'])
    op.create_index('ix_contacts_user_id', 'contacts', ['user_id'])
    op.create_index('ix_contacts_user_type', 'contacts', ['user_id', 'contact_type'])
    op.create_index('ix_contacts_user_name', 'contacts', ['user_id', 'name'])
    op.create_index('ix_contacts_user_active', 'contacts', ['user_id', 'is_active'])
    op.create_index('ix_contacts_email', 'contacts', ['email'])
    
    # Add contact_id to expenses table
    op.add_column('expenses', sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_expenses_contact_id', 'expenses', 'contacts', ['contact_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_expenses_contact_id', 'expenses', ['contact_id'])
    op.create_index('ix_expenses_user_contact', 'expenses', ['user_id', 'contact_id'])
    
    # Drop old constraint and add new one
    try:
        op.drop_constraint('ck_expense_invoice_requires_supplier', 'expenses', type_='check')
    except Exception:
        pass  # Constraint might not exist
    
    op.create_check_constraint('ck_expense_invoice_requires_contact', 'expenses', 
                               "expense_type = 'simple' OR (expense_type = 'invoice' AND contact_id IS NOT NULL)")
    
    # Remove old columns if they exist
    try:
        op.drop_column('expenses', 'supplier_name')
    except Exception:
        pass  # Column might not exist
    
    try:
        op.drop_column('expenses', 'supplier_tax_id')
    except Exception:
        pass  # Column might not exist


def downgrade() -> None:
    # Add back old columns
    op.add_column('expenses', sa.Column('supplier_name', sa.String(length=200), nullable=True))
    op.add_column('expenses', sa.Column('supplier_tax_id', sa.String(length=50), nullable=True))
    
    # Drop new constraint and add old one
    try:
        op.drop_constraint('ck_expense_invoice_requires_contact', 'expenses', type_='check')
    except Exception:
        pass  # Constraint might not exist
    
    op.create_check_constraint('ck_expense_invoice_requires_supplier', 'expenses',
                               "expense_type = 'simple' OR (expense_type = 'invoice' AND supplier_name IS NOT NULL)")
    
    # Remove contact_id from expenses
    try:
        op.drop_index('ix_expenses_user_contact', table_name='expenses')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_expenses_contact_id', table_name='expenses')
    except Exception:
        pass
    
    try:
        op.drop_constraint('fk_expenses_contact_id', 'expenses', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.drop_column('expenses', 'contact_id')
    except Exception:
        pass
    
    # Drop contacts table
    contact_indexes = [
        'ix_contacts_email',
        'ix_contacts_user_active', 
        'ix_contacts_user_name',
        'ix_contacts_user_type',
        'ix_contacts_user_id',
        'ix_contacts_contact_type',
        'ix_contacts_id'
    ]
    
    for index_name in contact_indexes:
        try:
            op.drop_index(index_name, table_name='contacts')
        except Exception:
            pass
    
    try:
        op.drop_table('contacts')
    except Exception:
        pass
    
    # No enum cleanup needed since we use string types 