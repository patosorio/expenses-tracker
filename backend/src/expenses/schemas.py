from datetime import datetime
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING, Annotated
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, field_validator, computed_field, ConfigDict

from .models import ExpenseType, PaymentMethod, PaymentStatus, AnalysisStatus


# Base Schemas
class ExpenseBase(BaseModel):
    description: str
    expense_date: datetime
    notes: Optional[str] = None
    receipt_url: Optional[str] = None
    expense_type: ExpenseType = ExpenseType.SIMPLE
    category_id: UUID
    payment_method: Optional[PaymentMethod] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_date: Optional[datetime] = None
    invoice_number: Optional[str] = None
    contact_id: Optional[UUID] = None
    payment_due_date: Optional[datetime] = None
    base_amount: Decimal
    tax_amount: Decimal = Decimal('0.00')
    total_amount: Decimal
    currency: str = 'EUR'
    tax_config_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        if len(v.strip()) > 500:
            raise ValueError('Description must be 500 characters or less')
        return v.strip()

    @field_validator('base_amount', 'total_amount')
    @classmethod
    def validate_positive_amounts(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @field_validator('tax_amount')
    @classmethod
    def validate_tax_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError('Tax amount cannot be negative')
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3 or not v.isalpha():
            raise ValueError('Currency must be a 3-letter ISO code')
        return v.upper()

    @field_validator('payment_date')
    @classmethod
    def validate_payment_date(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v is None:
            return v
        # Access expense_date from the model data
        expense_date = info.data.get('expense_date')
        if expense_date and v < expense_date:
            raise ValueError('Payment date cannot be before expense date')
        return v


class AttachmentBase(BaseModel):
    file_name: str
    file_url: str
    file_type: str
    file_size: int

    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('File size must be positive')
        if v > 52428800:  # 50MB
            raise ValueError('File size cannot exceed 50MB')
        return v


class DocumentAnalysisBase(BaseModel):
    original_filename: str
    file_url: Optional[str] = None
    file_type: str
    analysis_status: AnalysisStatus = AnalysisStatus.PENDING
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[Decimal] = None
    needs_review: bool = True

    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_score(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is None:
            return v
        if v < 0 or v > 1:
            raise ValueError('Confidence score must be between 0 and 1')
        return v


# Request Schemas
class SimpleExpenseCreate(BaseModel):
    """Schema for creating simple (receipt) expenses"""
    description: str
    expense_date: datetime
    expense_type: ExpenseType = ExpenseType.SIMPLE
    notes: Optional[str] = None
    receipt_url: Optional[str] = None
    category_id: UUID
    payment_method: PaymentMethod
    total_amount: Decimal
    currency: str = 'EUR'
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

    @field_validator('total_amount')
    @classmethod
    def validate_total_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Total amount must be positive')
        return v


class InvoiceExpenseCreate(BaseModel):
    """Schema for creating invoice expenses with tax calculations"""
    description: str
    expense_date: datetime
    expense_type: ExpenseType = ExpenseType.INVOICE
    notes: Optional[str] = None
    receipt_url: Optional[str] = None
    category_id: UUID
    payment_method: Optional[PaymentMethod] = None
    payment_due_date: Optional[datetime] = None
    invoice_number: Optional[str] = None
    contact_id: UUID
    base_amount: Decimal
    tax_config_id: Optional[UUID] = None
    currency: str = 'EUR'
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

    @field_validator('base_amount')
    @classmethod
    def validate_base_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Base amount must be positive')
        return v


class ExpenseUpdate(BaseModel):
    """Schema for updating expenses"""
    description: Optional[str] = None
    expense_date: Optional[datetime] = None
    notes: Optional[str] = None
    receipt_url: Optional[str] = None
    category_id: Optional[UUID] = None
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = None
    payment_date: Optional[datetime] = None
    invoice_number: Optional[str] = None
    contact_id: Optional[UUID] = None
    payment_due_date: Optional[datetime] = None
    base_amount: Optional[Decimal] = None
    tax_config_id: Optional[UUID] = None
    currency: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        if len(v.strip()) > 500:
            raise ValueError('Description must be 500 characters or less')
        return v.strip()

    @field_validator('base_amount')
    @classmethod
    def validate_base_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is None:
            return v
        if v <= 0:
            raise ValueError('Base amount must be positive')
        return v


class AttachmentCreate(AttachmentBase):
    """Schema for creating attachments"""
    pass


class DocumentAnalysisCreate(DocumentAnalysisBase):
    """Schema for creating document analysis"""
    pass


class AttachmentResponse(AttachmentBase):
    """Schema for attachment responses"""
    id: UUID
    expense_id: UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentAnalysisResponse(DocumentAnalysisBase):
    """Schema for document analysis responses"""
    id: UUID
    expense_id: Optional[UUID] = None
    user_id: str
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExpenseResponse(ExpenseBase):
    """Complete expense response with relationships"""
    id: UUID
    user_id: str
    is_overdue: bool
    days_overdue: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    # Related objects - made optional to avoid async loading issues
    contact: Optional[Dict[str, Any]] = None  # Using Dict instead of ContactResponse to avoid circular import
    attachments: Optional[List[AttachmentResponse]] = None
    document_analysis: Optional[DocumentAnalysisResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ExpenseCreateResponse(BaseModel):
    """Simplified expense response for creation endpoints"""
    id: UUID
    description: str
    expense_date: datetime
    expense_type: ExpenseType
    notes: Optional[str] = None
    receipt_url: Optional[str] = None
    category_id: UUID
    payment_method: Optional[PaymentMethod] = None
    payment_status: PaymentStatus
    payment_date: Optional[datetime] = None
    invoice_number: Optional[str] = None
    contact_id: Optional[UUID] = None
    payment_due_date: Optional[datetime] = None
    base_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    tax_config_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    user_id: str
    is_overdue: bool
    days_overdue: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ExpenseListResponse(BaseModel):
    """Optimized expense response for listing"""
    id: UUID
    description: str
    expense_date: datetime
    expense_type: ExpenseType
    contact_id: Optional[UUID] = None
    base_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    payment_status: PaymentStatus
    payment_date: Optional[datetime] = None
    is_overdue: bool
    days_overdue: int
    category_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


class ExpensePreviewResponse(BaseModel):
    """Pre-filled expense data from OCR analysis"""
    description: Optional[str] = None
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    expense_date: Optional[datetime] = None
    payment_due_date: Optional[datetime] = None
    base_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    suggested_category: Optional[str] = None
    confidence_score: Decimal


class ExpenseFilter(BaseModel):
    """Advanced filtering options for expenses"""
    expense_type: Optional[ExpenseType] = None
    payment_status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    category_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    overdue_only: bool = False
    tags: Optional[List[str]] = None
    search: Optional[str] = None


class ExpenseSummary(BaseModel):
    """Expense summary by period/category"""
    period: str
    total_expenses: Decimal
    total_count: int
    average_expense: Decimal
    by_category: Dict[str, Decimal]
    by_payment_method: Dict[PaymentMethod, Decimal]
    by_type: Dict[ExpenseType, Decimal]
    currency: str


class ExpenseStats(BaseModel):
    """Statistical aggregations for dashboard"""
    total_expenses: Decimal
    total_count: int
    pending_payments: Decimal
    overdue_count: int
    overdue_amount: Decimal
    this_month_total: Decimal
    last_month_total: Decimal
    monthly_change_percent: Decimal
    top_categories: List[Dict[str, Any]]
    top_suppliers: List[Dict[str, Any]]


class OverdueExpenseResponse(BaseModel):
    """Response for overdue invoice tracking"""
    id: UUID
    description: str
    contact_name: str
    invoice_number: Optional[str]
    total_amount: Decimal
    payment_due_date: datetime
    days_overdue: int
    currency: str

    model_config = ConfigDict(from_attributes=True)


class OverdueExpensesListResponse(BaseModel):
    """Response for list of overdue expenses"""
    overdue_invoices: List[OverdueExpenseResponse]
    total_overdue_amount: Decimal
    count: int
    currency: str


class ExpenseListPaginatedResponse(BaseModel):
    """Paginated expense list response"""
    expenses: List[ExpenseListResponse]
    total: int
    page: int
    per_page: int
    pages: int
