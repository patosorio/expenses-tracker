"""
Expense Management Module

This module provides comprehensive expense management functionality including:
- Simple (receipt) and invoice expense types
- Automatic tax calculations with user-configurable tax rates
- Google Vision API integration for document analysis and OCR
- File attachment management
- Advanced filtering and analytics
- Overdue invoice tracking
- Multi-currency support
"""

from .models import (
    Expense,
    DocumentAnalysis,
    ExpenseAttachment,
    ExpenseType,
    PaymentMethod,
    PaymentStatus,
    AnalysisStatus
)
from src.business.models import TaxConfiguration

from .schemas import (
    # Request schemas
    SimpleExpenseCreate,
    InvoiceExpenseCreate,
    ExpenseUpdate,
    AttachmentCreate,
    DocumentAnalysisCreate,
    ExpenseFilter,
    
    # Response schemas
    ExpenseResponse,
    ExpenseListResponse,
    ExpenseListPaginatedResponse,
    AttachmentResponse,
    DocumentAnalysisResponse,
    ExpensePreviewResponse,
    OverdueExpensesListResponse,
    ExpenseStats,
    ExpenseSummary
)

from .service import ExpenseService
from .routes import router as expenses_router

__all__ = [
    # Models
    "Expense",
    "DocumentAnalysis",
    "ExpenseAttachment",
    "ExpenseType",
    "PaymentMethod",
    "PaymentStatus",
    "AnalysisStatus",
    
    # Schemas
    "SimpleExpenseCreate",
    "InvoiceExpenseCreate",
    "ExpenseUpdate",
    "AttachmentCreate",
    "DocumentAnalysisCreate",
    "ExpenseFilter",
    "ExpenseResponse",
    "ExpenseListResponse",
    "ExpenseListPaginatedResponse",
    "AttachmentResponse",
    "DocumentAnalysisResponse",
    "ExpensePreviewResponse",
    "OverdueExpensesListResponse",
    "ExpenseStats",
    "ExpenseSummary",
    
    # Service
    "ExpenseService",
    
    # Router
    "expenses_router"
]
