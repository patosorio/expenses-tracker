"""Add categories table with hierarchical structure

Revision ID: add_categories
Revises: 4bb87dcc8dee
Create Date: 2025-07-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_categories'
down_revision: Union[str, Sequence[str], None] = '4bb87dcc8dee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create CategoryType enum only if it doesn't exist
    connection = op.get_bind()
    
    # Check if enum exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_type WHERE typname = 'categorytype'
    """)).fetchone()
    
    if not result:
        categorytype_enum = postgresql.ENUM('EXPENSE', 'INCOME', name='categorytype')
        categorytype_enum.create(connection)
    
    # Check if categories table already exists
    table_exists = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'categories'
    """)).fetchone()
    
    if table_exists:
        return  # Table already exists, skip migration
    
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                 primary_key=True, 
                 server_default=sa.text('gen_random_uuid()'),
                 nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.Enum('EXPENSE', 'INCOME', name='categorytype'), nullable=False),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(10), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False, nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "type IN ('EXPENSE', 'INCOME')",
            name='ck_category_type'
        ),
        sa.CheckConstraint(
            "color IS NULL OR color ~ '^#[0-9A-Fa-f]{6}$'",
            name='ck_category_color_format'
        ),
        sa.CheckConstraint(
            'id != parent_id',
            name='ck_category_no_self_reference'
        ),
        
        # Unique constraint
        sa.UniqueConstraint('user_id', 'name', 'parent_id', 
                           name='uq_category_name_per_level')
    )
    
    # Create indexes
    op.create_index('ix_categories_id', 'categories', ['id'])
    op.create_index('ix_categories_user_id', 'categories', ['user_id'])
    op.create_index('ix_categories_parent_id', 'categories', ['parent_id'])
    op.create_index('ix_categories_user_parent', 'categories', ['user_id', 'parent_id'])
    op.create_index('ix_categories_user_type', 'categories', ['user_id', 'type'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes (if they exist)
    connection = op.get_bind()
    
    try:
        op.drop_index('ix_categories_user_type', 'categories')
    except:
        pass
    try:
        op.drop_index('ix_categories_user_parent', 'categories')
    except:
        pass
    try:
        op.drop_index('ix_categories_parent_id', 'categories')
    except:
        pass
    try:
        op.drop_index('ix_categories_user_id', 'categories')
    except:
        pass
    try:
        op.drop_index('ix_categories_id', 'categories')
    except:
        pass
    
    # Drop table (if it exists)
    try:
        op.drop_table('categories')
    except:
        pass
    
    # Drop enum only if it exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_type WHERE typname = 'categorytype'
    """)).fetchone()
    
    if result:
        categorytype_enum = postgresql.ENUM('EXPENSE', 'INCOME', name='categorytype')
        categorytype_enum.drop(connection) 