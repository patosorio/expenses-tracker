from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index, Enum, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import text
from datetime import datetime, date
from enum import Enum as PyEnum
from decimal import Decimal

from src.database import Base


class ExpenseType(str, PyEnum):
    simple = "simple"  # Receipt-type expenses, paid immediately
    invoice = "invoice"  # Invoice-type expenses with payment terms


class PaymentMethod(str, PyEnum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"


class AnalysisStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"





class Expense(Base):
    """Main expense model supporting both simple receipts and invoices"""
    __tablename__ = "expenses"

    # Primary key with PostgreSQL UUID
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Basic expense fields
    description = Column(String(500), nullable=False)
    expense_date = Column(DateTime(timezone=True), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    receipt_url = Column(String(500), nullable=True)
    expense_type = Column(Enum(ExpenseType), nullable=False, default=ExpenseType.simple)
    
    # Multitenant support
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Category relationship
    category_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Payment fields
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Invoice-specific fields
    invoice_number = Column(String(100), nullable=True)
    payment_due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Contact relationship (for vendors/suppliers)
    contact_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Financial fields - using Decimal for precision
    base_amount = Column(Numeric(10, 2), nullable=False)  # Amount before tax
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)  # Calculated tax
    total_amount = Column(Numeric(10, 2), nullable=False)  # Total including tax
    currency = Column(String(3), nullable=False, default='EUR')  # ISO currency code
    
    # Tax configuration relationship
    tax_config_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("tax_configurations.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Metadata fields
    tags = Column(JSON, nullable=True)  # Array of strings
    custom_fields = Column(JSON, nullable=True)  # Flexible custom data
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User")
    category = relationship("Category")
    contact = relationship("Contact", back_populates="expenses")
    tax_config = relationship("TaxConfiguration", back_populates="expenses")
    attachments = relationship("ExpenseAttachment", back_populates="expense", cascade="all, delete-orphan")
    document_analysis = relationship("DocumentAnalysis", back_populates="expense", uselist=False, cascade="all, delete-orphan")
    
    # Table constraints
    __table_args__ = (
        # Amount validation
        CheckConstraint(
            'base_amount > 0',
            name='ck_expense_base_amount_positive'
        ),
        CheckConstraint(
            'tax_amount >= 0',
            name='ck_expense_tax_amount_non_negative'
        ),
        CheckConstraint(
            'total_amount > 0',
            name='ck_expense_total_amount_positive'
        ),
        
        # Business logic constraints
        CheckConstraint(
            "expense_type = 'simple' OR (expense_type = 'invoice' AND contact_id IS NOT NULL)",
            name='ck_expense_invoice_requires_contact'
        ),
        CheckConstraint(
            "payment_date IS NULL OR payment_date >= expense_date",
            name='ck_expense_payment_after_expense_date'
        ),
        CheckConstraint(
            "expense_date <= CURRENT_DATE",
            name='ck_expense_date_not_future'
        ),
        
        # Currency validation
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name='ck_expense_currency_format'
        ),
        
        # Performance indexes
        Index('ix_expenses_user_date', 'user_id', 'expense_date'),
        Index('ix_expenses_user_category', 'user_id', 'category_id'),
        Index('ix_expenses_user_contact', 'user_id', 'contact_id'),
        Index('ix_expenses_user_type', 'user_id', 'expense_type'),
        Index('ix_expenses_user_status', 'user_id', 'payment_status'),
        Index('ix_expenses_overdue', 'user_id', 'payment_due_date', 'payment_status'),
        Index('ix_expenses_user_active', 'user_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Expense(id={self.id}, description={self.description}, total={self.total_amount} {self.currency})>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if expense is overdue (invoices only)"""
        if self.expense_type != ExpenseType.INVOICE:
            return False
        if self.payment_status == PaymentStatus.PAID:
            return False
        if not self.payment_due_date:
            return False
        return datetime.now(self.payment_due_date.tzinfo) > self.payment_due_date
    
    @property
    def days_overdue(self) -> int:
        """Calculate days overdue (invoices only)"""
        if not self.is_overdue:
            return 0
        delta = datetime.now(self.payment_due_date.tzinfo) - self.payment_due_date
        return delta.days
    
    def calculate_tax_amount(self, tax_rate: Decimal) -> Decimal:
        """Calculate tax amount based on base amount and tax rate"""
        return (self.base_amount * tax_rate / 100).quantize(Decimal('0.01'))
    
    def update_total_amount(self) -> None:
        """Update total amount based on base and tax amounts"""
        self.total_amount = self.base_amount + self.tax_amount


class DocumentAnalysis(Base):
    """Google Vision API document analysis results"""
    __tablename__ = "document_analyses"

    # Primary key with PostgreSQL UUID
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Link to expense (nullable for pre-creation analysis)
    expense_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # User reference for pre-creation analysis
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=True)  # Cloud storage URL
    file_type = Column(String(50), nullable=False)  # MIME type
    
    # Analysis status and results
    analysis_status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING)
    extracted_data = Column(JSON, nullable=True)  # Structured extracted data
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    needs_review = Column(Boolean, default=True)
    
    # Processing metadata
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    expense = relationship("Expense", back_populates="document_analysis")
    user = relationship("User")
    
    # Table constraints
    __table_args__ = (
        # Confidence score validation
        CheckConstraint(
            'confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)',
            name='ck_analysis_confidence_range'
        ),
        
        # Performance indexes
        Index('ix_document_analyses_user_status', 'user_id', 'analysis_status'),
        Index('ix_document_analyses_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<DocumentAnalysis(id={self.id}, filename={self.original_filename}, status={self.analysis_status})>"


class ExpenseAttachment(Base):
    """File attachments for expenses"""
    __tablename__ = "expense_attachments"

    # Primary key with PostgreSQL UUID
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Link to expense
    expense_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # File information
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)  # Cloud storage URL
    file_type = Column(String(50), nullable=False)  # MIME type
    file_size = Column(Numeric(12, 0), nullable=False)  # Size in bytes
    
    # Audit fields
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    expense = relationship("Expense", back_populates="attachments")
    
    # Table constraints
    __table_args__ = (
        # File size validation (max 50MB)
        CheckConstraint(
            'file_size > 0 AND file_size <= 52428800',
            name='ck_attachment_file_size'
        ),
        
        # Performance indexes
        Index('ix_attachments_expense', 'expense_id'),
    )
    
    def __repr__(self):
        return f"<ExpenseAttachment(id={self.id}, filename={self.file_name}, size={self.file_size})>"
