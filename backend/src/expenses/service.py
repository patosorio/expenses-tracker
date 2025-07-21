from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from sqlalchemy import select
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import json
import logging

from .models import (
    Expense, DocumentAnalysis, ExpenseAttachment,
    ExpenseType, PaymentMethod, PaymentStatus, AnalysisStatus
)
from .repository import ExpenseRepository
from ..business.service import BusinessService
from .schemas import (
    SimpleExpenseCreate, InvoiceExpenseCreate, ExpenseUpdate,
    AttachmentCreate, DocumentAnalysisCreate,
    ExpenseFilter, ExpenseSummary, ExpenseStats, ExpensePreviewResponse,
    OverdueExpensesListResponse, OverdueExpenseResponse
)
from ..categories.models import Category, CategoryType
from ..users.models import User
from ..core.database import get_db
from .exceptions import (
    ExpenseNotFoundError, ExpenseValidationError, InvalidExpenseTypeError,
    InvalidPaymentStatusError, DocumentAnalysisNotFoundError, AttachmentNotFoundError,
    InvalidTaxCalculationError, ExpenseUpdateError, ExpenseDeleteError
)

logger = logging.getLogger(__name__)


class ExpenseService:
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.expense_repo = ExpenseRepository(db)

    # Core CRUD Operations
    async def create_simple_expense(
            self,
            user_id: str,
            expense_data: SimpleExpenseCreate,
            contact_id: Optional[str] = None
        ) -> Expense:
        """Create a simple (receipt) expense with automatic payment date setting"""
        try:
            # Validate category belongs to user and is expense type
            await self._validate_user_category(user_id, expense_data.category_id)
            
            # Debug: Log the payment method value
            logger.info(f"Creating expense with payment_method: {expense_data.payment_method} (type: {type(expense_data.payment_method)})")
            
            # Business logic: For simple expenses: base_amount = total_amount, tax_amount = 0, payment_date = expense_date
            expense = Expense(
                id=uuid.uuid4(),
                user_id=user_id,
                description=expense_data.description,
                expense_date=expense_data.expense_date,
                notes=expense_data.notes,
                receipt_url=expense_data.receipt_url,
                expense_type=ExpenseType.SIMPLE,
                category_id=expense_data.category_id,
                payment_method=expense_data.payment_method,
                payment_status=PaymentStatus.PAID,  # Business rule: simple expenses are paid immediately
                payment_date=expense_data.expense_date,  # Business rule: payment date = expense date
                base_amount=expense_data.total_amount,  # Business rule: base = total for simple expenses
                tax_amount=Decimal('0.00'),  # Business rule: no tax for simple expenses
                total_amount=expense_data.total_amount,
                currency=expense_data.currency,
                tags=expense_data.tags,
                custom_fields=expense_data.custom_fields
            )
            
            # Delegate to repository for data access
            return await self.expense_repo.create(expense)
            
        except Exception as e:
            logger.error(f"Error creating simple expense for user {user_id}: {str(e)}")
            raise ExpenseValidationError(f"Failed to create expense: {str(e)}")

    async def create_invoice_expense(self, user_id: str, expense_data: InvoiceExpenseCreate) -> Expense:
        """Create an invoice expense with automatic tax calculation"""
        try:
            # Validate category belongs to user and is expense type
            await self._validate_user_category(user_id, expense_data.category_id)
            
            # Business logic: Calculate tax if tax_config_id provided
            tax_amount = Decimal('0.00')
            tax_config = None
            
            if expense_data.tax_config_id:
                business_service = BusinessService(self.db)
                tax_config = await business_service.get_tax_configuration(str(expense_data.tax_config_id), user_id)
                if tax_config:
                    tax_amount = self._calculate_tax_amount(expense_data.base_amount, tax_config.rate)
            
            total_amount = expense_data.base_amount + tax_amount
            
            expense = Expense(
                id=uuid.uuid4(),
                user_id=user_id,
                description=expense_data.description,
                expense_date=expense_data.expense_date,
                notes=expense_data.notes,
                receipt_url=expense_data.receipt_url,
                expense_type=ExpenseType.INVOICE,
                category_id=expense_data.category_id,
                payment_method=expense_data.payment_method,
                payment_status=PaymentStatus.PENDING,  # Business rule: invoices start as pending
                payment_date=None,  # Business rule: not paid yet
                invoice_number=expense_data.invoice_number,
                contact_id=expense_data.contact_id,
                payment_due_date=expense_data.payment_due_date,
                base_amount=expense_data.base_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                currency=expense_data.currency,
                tax_config_id=expense_data.tax_config_id,
                tags=expense_data.tags,
                custom_fields=expense_data.custom_fields
            )
            
            # Delegate to repository for data access
            return await self.expense_repo.create(expense)
            
        except Exception as e:
            logger.error(f"Error creating invoice expense for user {user_id}: {str(e)}")
            raise ExpenseValidationError(f"Failed to create invoice expense: {str(e)}")

    async def get_expense_by_id(self, user_id: str, expense_id: uuid.UUID) -> Optional[Expense]:
        """Get expense by ID with full relationships"""
        return await self.expense_repo.get_by_id(user_id, expense_id)

    async def update_expense(self, user_id: str, expense_id: uuid.UUID, expense_data: ExpenseUpdate) -> Expense:
        """Update expense with tax recalculation if needed"""
        try:
            expense = await self.get_expense_by_id(user_id, expense_id)
            if not expense:
                raise ExpenseNotFoundError("Expense not found")
            
            # Business logic: Validate category if provided
            if expense_data.category_id:
                await self._validate_user_category(user_id, expense_data.category_id)
            
            # Business logic: Recalculate tax if base_amount or tax_config_id changed
            update_data = expense_data.model_dump(exclude_unset=True)
            
            if 'base_amount' in update_data or 'tax_config_id' in update_data:
                base_amount = update_data.get('base_amount', expense.base_amount)
                tax_config_id = update_data.get('tax_config_id', expense.tax_config_id)
                
                if tax_config_id and expense.expense_type == ExpenseType.INVOICE:
                    business_service = BusinessService(self.db)
                    tax_config = await business_service.get_tax_configuration(str(tax_config_id), user_id)
                    if tax_config:
                        tax_amount = self._calculate_tax_amount(base_amount, tax_config.rate)
                        update_data['tax_amount'] = tax_amount
                        update_data['total_amount'] = base_amount + tax_amount
                
            # Apply updates
            for field, value in update_data.items():
                setattr(expense, field, value)
            
            # Delegate to repository for data access
            return await self.expense_repo.update(expense)
            
        except Exception as e:
            logger.error(f"Error updating expense {expense_id} for user {user_id}: {str(e)}")
            raise ExpenseUpdateError(f"Failed to update expense: {str(e)}")

    async def delete_expense(self, user_id: str, expense_id: uuid.UUID) -> bool:
        """Soft delete expense with attachment cleanup"""
        try:
            expense = await self.get_expense_by_id(user_id, expense_id)
            if not expense:
                raise ExpenseNotFoundError("Expense not found")
            
            # Business logic: Check if expense can be deleted
            if expense.payment_status == PaymentStatus.PAID and expense.expense_type == ExpenseType.INVOICE:
                # For paid invoices, we might want to prevent deletion or require special handling
                logger.warning(f"Attempting to delete paid invoice {expense_id} for user {user_id}")
            
            # Delegate to repository for data access
            return await self.expense_repo.delete(expense)
            
        except Exception as e:
            logger.error(f"Error deleting expense {expense_id} for user {user_id}: {str(e)}")
            raise ExpenseDeleteError(f"Failed to delete expense: {str(e)}")

    async def mark_expense_as_paid(self, user_id: str, expense_id: uuid.UUID, payment_date: Optional[datetime] = None) -> Expense:
        """Mark expense as paid and set payment date"""
        try:
            expense = await self.get_expense_by_id(user_id, expense_id)
            if not expense:
                raise ExpenseNotFoundError("Expense not found")
            
            # Business logic: Validate payment status transition
            if expense.payment_status == PaymentStatus.PAID:
                raise InvalidPaymentStatusError("Expense is already marked as paid")
            
            # Business logic: Set payment status and date
            expense.payment_status = PaymentStatus.PAID
            expense.payment_date = payment_date or datetime.utcnow()
            
            # Delegate to repository for data access
            return await self.expense_repo.update(expense)
            
        except Exception as e:
            logger.error(f"Error marking expense {expense_id} as paid for user {user_id}: {str(e)}")
            raise ExpenseUpdateError(f"Failed to mark expense as paid: {str(e)}")

    # Advanced Query Operations
    async def get_expenses_with_filters(
        self,
        user_id: str,
        filters: ExpenseFilter,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "expense_date",
        sort_order: str = "desc"
    ) -> Tuple[List[Expense], int]:
        """Get expenses with advanced filtering and sorting"""
        try:
            # Delegate to repository for data access
            return await self.expense_repo.get_with_filters(
                user_id, filters, skip, limit, sort_by, sort_order
            )
            
        except Exception as e:
            logger.error(f"Error getting expenses with filters for user {user_id}: {str(e)}")
            raise

    async def get_overdue_expenses(self, user_id: str) -> OverdueExpensesListResponse:
        """Get all overdue invoice expenses"""
        try:
            # Delegate to repository for data access
            return await self.expense_repo.get_overdue_expenses(user_id)
            
        except Exception as e:
            logger.error(f"Error getting overdue expenses for user {user_id}: {str(e)}")
            raise

    async def get_expenses_paginated(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "expense_date",
        sort_order: str = "desc"
    ) -> Tuple[List[Expense], int]:
        """Simple paginated expenses without complex filtering"""
        try:
            # Delegate to repository for data access
            return await self.expense_repo.get_paginated(
                user_id, skip, limit, sort_by, sort_order
            )
        except Exception as e:
            logger.error(f"Error getting paginated expenses for user {user_id}: {str(e)}")
            raise

    async def get_expenses_by_type(
        self,
        user_id: str,
        expense_type: ExpenseType,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Expense], int]:
        """Get expenses by type (simple or invoice)"""
        try:
            # Delegate to repository for data access
            return await self.expense_repo.get_by_type(
                user_id, expense_type, skip, limit
            )
        except Exception as e:
            logger.error(f"Error getting {expense_type} expenses for user {user_id}: {str(e)}")
            raise
       
    # Document Analysis & OCR
    async def create_document_analysis(self, user_id: str, analysis_data: DocumentAnalysisCreate) -> DocumentAnalysis:
        """Create document analysis record for OCR processing"""
        try:
            # Business logic: Create document analysis model
            analysis = DocumentAnalysis(
                id=uuid.uuid4(),
                user_id=user_id,
                **analysis_data.model_dump()
            )
            
            # Delegate to repository for data access
            return await self.expense_repo.create_document_analysis(analysis)
            
        except Exception as e:
            logger.error(f"Error creating document analysis for user {user_id}: {str(e)}")
            raise

    async def update_analysis_status(
        self,
        analysis_id: uuid.UUID,
        status: AnalysisStatus,
        extracted_data: Optional[Dict[str, Any]] = None,
        confidence_score: Optional[Decimal] = None,
        error_message: Optional[str] = None
    ) -> DocumentAnalysis:
        """Update document analysis status and results"""
        try:
            # Get analysis from repository
            analysis = await self.expense_repo.get_document_analysis_by_id(analysis_id)
            if not analysis:
                raise DocumentAnalysisNotFoundError("Document analysis not found")
            
            # Business logic: Update analysis status and fields
            analysis.analysis_status = status
            if extracted_data:
                analysis.extracted_data = extracted_data
            if confidence_score is not None:
                analysis.confidence_score = confidence_score
            if error_message:
                analysis.error_message = error_message
            
            # Business logic: Set processing timestamps
            if status == AnalysisStatus.PROCESSING:
                analysis.processing_started_at = datetime.utcnow()
            elif status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                analysis.processing_completed_at = datetime.utcnow()
            
            # Delegate to repository for data access
            return await self.expense_repo.update_document_analysis(analysis)
            
        except Exception as e:
            logger.error(f"Error updating analysis status for {analysis_id}: {str(e)}")
            raise

    async def create_expense_from_analysis(
        self,
        user_id: str,
        analysis_id: uuid.UUID,
        user_corrections: Optional[Dict[str, Any]] = None
    ) -> Expense:
        """Create expense from OCR analysis results"""
        try:
            # Get analysis from repository
            analysis = await self.expense_repo.get_document_analysis_by_id(analysis_id)
            
            if not analysis or not analysis.extracted_data:
                raise ExpenseValidationError("Analysis not found or no extracted data available")
            
            extracted = analysis.extracted_data
            
            # Business logic: Apply user corrections
            if user_corrections:
                extracted.update(user_corrections)
            
            # Business logic: Determine expense type based on extracted data
            expense_type = ExpenseType.INVOICE if extracted.get('invoice_number') else ExpenseType.SIMPLE
            
            # Business logic: Create expense based on type
            if expense_type == ExpenseType.INVOICE:
                # Invoice creation requires a contact_id
                if not extracted.get('contact_id'):
                    raise ExpenseValidationError("Invoice expenses require a contact_id. Please specify a contact in user_corrections.")
                
                # Find default tax config for tax calculation
                business_service = BusinessService(self.db)
                tax_configs = await business_service.get_tax_configurations(user_id, active_only=True)
                tax_config = next((tc for tc in tax_configs if tc.is_default), None)
                tax_config_id = tax_config.id if tax_config else None
                
                expense_data = InvoiceExpenseCreate(
                    description=extracted.get('description', 'Imported from document'),
                    expense_date=extracted.get('expense_date', datetime.utcnow()),
                    contact_id=uuid.UUID(extracted['contact_id']),
                    invoice_number=extracted.get('invoice_number'),
                    base_amount=Decimal(str(extracted.get('base_amount', 0))),
                    tax_config_id=tax_config_id,
                    category_id=uuid.UUID(extracted['category_id']),  # Must be provided
                    payment_due_date=extracted.get('payment_due_date')
                )
                expense = await self.create_invoice_expense(user_id, expense_data)
            else:
                expense_data = SimpleExpenseCreate(
                    description=extracted.get('description', 'Imported from document'),
                    expense_date=extracted.get('expense_date', datetime.utcnow()),
                    total_amount=Decimal(str(extracted.get('total_amount', 0))),
                    payment_method=PaymentMethod.CARD,  # Default
                    category_id=uuid.UUID(extracted['category_id'])  # Must be provided
                )
                expense = await self.create_simple_expense(user_id, expense_data)
            
            # Business logic: Link analysis to expense
            analysis.expense_id = expense.id
            await self.expense_repo.update_document_analysis(analysis)
            
            logger.info(f"Created expense {expense.id} from analysis {analysis_id}")
            return expense
            
        except Exception as e:
            logger.error(f"Error creating expense from analysis {analysis_id}: {str(e)}")
            raise

    # Analytics & Reporting
    async def get_expense_stats(self, user_id: str) -> ExpenseStats:
        """Get comprehensive expense statistics"""
        try:
            # Delegate to repository for data access
            return await self.expense_repo.get_stats(user_id)
            
        except Exception as e:
            logger.error(f"Error getting expense stats for user {user_id}: {str(e)}")
            raise

    # File Management
    async def add_attachment(self, user_id: str, expense_id: uuid.UUID, attachment_data: AttachmentCreate) -> ExpenseAttachment:
        """Add file attachment to expense"""
        try:
            # Business logic: Verify expense belongs to user
            expense = await self.get_expense_by_id(user_id, expense_id)
            if not expense:
                raise ExpenseNotFoundError("Expense not found")
            
            # Business logic: Create attachment model
            attachment = ExpenseAttachment(
                id=uuid.uuid4(),
                expense_id=expense_id,
                **attachment_data.model_dump()
            )
            
            # Delegate to repository for data access
            return await self.expense_repo.create_attachment(attachment)
            
        except Exception as e:
            logger.error(f"Error adding attachment to expense {expense_id}: {str(e)}")
            raise

    # Helper Methods
    async def _validate_user_category(self, user_id: str, category_id: uuid.UUID) -> Category:
        """Validate that category belongs to user and is expense type"""
        # Business logic: Validate category belongs to user and is expense type
        
        query = select(Category).where(
            and_(
                Category.id == category_id,
                Category.user_id == user_id,
                Category.type == CategoryType.EXPENSE,
                Category.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        
        if not category:
            raise ExpenseValidationError("Invalid category: must be an active expense category belonging to the user")
        
        return category

    async def _calculate_tax_amount(self, base_amount: Decimal, tax_rate: Decimal) -> Decimal:
        """Calculate tax amount with proper rounding"""
        # Business logic: Calculate tax amount with proper rounding
        return (base_amount * tax_rate / 100).quantize(Decimal('0.01'))


