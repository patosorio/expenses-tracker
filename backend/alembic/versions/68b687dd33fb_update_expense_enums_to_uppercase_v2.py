"""update_expense_enums_to_uppercase_v2

Revision ID: 68b687dd33fb
Revises: 7f8c9d4e5b2a
Create Date: 2025-07-19 20:45:12.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68b687dd33fb'
down_revision: Union[str, Sequence[str], None] = '7f8c9d4e5b2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop and recreate expense_type enum
    op.execute("DROP TYPE IF EXISTS expensetype CASCADE")
    op.execute("CREATE TYPE expensetype AS ENUM ('SIMPLE', 'INVOICE')")
    
    # Drop and recreate payment_method enum
    op.execute("DROP TYPE IF EXISTS paymentmethod CASCADE")
    op.execute("CREATE TYPE paymentmethod AS ENUM ('CASH', 'CARD', 'BANK_TRANSFER', 'DIGITAL_WALLET')")
    
    # Drop and recreate payment_status enum
    op.execute("DROP TYPE IF EXISTS paymentstatus CASCADE")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('PENDING', 'PAID', 'REFUNDED')")
    
    # Drop and recreate analysis_status enum
    op.execute("DROP TYPE IF EXISTS analysisstatus CASCADE")
    op.execute("CREATE TYPE analysisstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')")
    
    # Update existing data in expenses table
    op.execute("UPDATE expenses SET expense_type = 'SIMPLE' WHERE expense_type = 'simple'")
    op.execute("UPDATE expenses SET expense_type = 'INVOICE' WHERE expense_type = 'invoice'")
    
    op.execute("UPDATE expenses SET payment_method = 'CASH' WHERE payment_method = 'cash'")
    op.execute("UPDATE expenses SET payment_method = 'CARD' WHERE payment_method = 'card'")
    op.execute("UPDATE expenses SET payment_method = 'BANK_TRANSFER' WHERE payment_method = 'bank_transfer'")
    op.execute("UPDATE expenses SET payment_method = 'DIGITAL_WALLET' WHERE payment_method = 'digital_wallet'")
    
    op.execute("UPDATE expenses SET payment_status = 'PENDING' WHERE payment_status = 'pending'")
    op.execute("UPDATE expenses SET payment_status = 'PAID' WHERE payment_status = 'paid'")
    op.execute("UPDATE expenses SET payment_status = 'REFUNDED' WHERE payment_status = 'refunded'")
    
    # Update existing data in document_analyses table
    op.execute("UPDATE document_analyses SET analysis_status = 'PENDING' WHERE analysis_status = 'pending'")
    op.execute("UPDATE document_analyses SET analysis_status = 'PROCESSING' WHERE analysis_status = 'processing'")
    op.execute("UPDATE document_analyses SET analysis_status = 'COMPLETED' WHERE analysis_status = 'completed'")
    op.execute("UPDATE document_analyses SET analysis_status = 'FAILED' WHERE analysis_status = 'failed'")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop and recreate expense_type enum with lowercase values
    op.execute("DROP TYPE IF EXISTS expensetype CASCADE")
    op.execute("CREATE TYPE expensetype AS ENUM ('simple', 'invoice')")
    
    # Drop and recreate payment_method enum with lowercase values
    op.execute("DROP TYPE IF EXISTS paymentmethod CASCADE")
    op.execute("CREATE TYPE paymentmethod AS ENUM ('cash', 'card', 'bank_transfer', 'digital_wallet')")
    
    # Drop and recreate payment_status enum with lowercase values
    op.execute("DROP TYPE IF EXISTS paymentstatus CASCADE")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('pending', 'paid', 'refunded')")
    
    # Drop and recreate analysis_status enum with lowercase values
    op.execute("DROP TYPE IF EXISTS analysisstatus CASCADE")
    op.execute("CREATE TYPE analysisstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    
    # Update existing data in expenses table back to lowercase
    op.execute("UPDATE expenses SET expense_type = 'simple' WHERE expense_type = 'SIMPLE'")
    op.execute("UPDATE expenses SET expense_type = 'invoice' WHERE expense_type = 'INVOICE'")
    
    op.execute("UPDATE expenses SET payment_method = 'cash' WHERE payment_method = 'CASH'")
    op.execute("UPDATE expenses SET payment_method = 'card' WHERE payment_method = 'CARD'")
    op.execute("UPDATE expenses SET payment_method = 'bank_transfer' WHERE payment_method = 'BANK_TRANSFER'")
    op.execute("UPDATE expenses SET payment_method = 'digital_wallet' WHERE payment_method = 'DIGITAL_WALLET'")
    
    op.execute("UPDATE expenses SET payment_status = 'pending' WHERE payment_status = 'PENDING'")
    op.execute("UPDATE expenses SET payment_status = 'paid' WHERE payment_status = 'PAID'")
    op.execute("UPDATE expenses SET payment_status = 'refunded' WHERE payment_status = 'REFUNDED'")
    
    # Update existing data in document_analyses table back to lowercase
    op.execute("UPDATE document_analyses SET analysis_status = 'pending' WHERE analysis_status = 'PENDING'")
    op.execute("UPDATE document_analyses SET analysis_status = 'processing' WHERE analysis_status = 'PROCESSING'")
    op.execute("UPDATE document_analyses SET analysis_status = 'completed' WHERE analysis_status = 'COMPLETED'")
    op.execute("UPDATE document_analyses SET analysis_status = 'failed' WHERE analysis_status = 'FAILED'")
