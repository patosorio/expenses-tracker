from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import uuid
import logging
import re
from .models import (
    Expense, DocumentAnalysis, ExpenseAttachment,
    ExpenseType, PaymentMethod, PaymentStatus, AnalysisStatus
)
from .repository import ExpenseRepository
from ..business.service import BusinessService
from .schemas import *
from ..categories.models import Category, CategoryType
from .exceptions import *
from ..core.shared.exceptions import ValidationError, InternalServerError

logger = logging.getLogger(__name__)


# Business constants
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD"]
MAX_FILE_SIZE_MB = 10
SUPPORTED_FILE_TYPES = ["image/jpeg", "image/png", "image/gif", "application/pdf"]


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
        """Create a simple (receipt) expense with comprehensive validation."""
        try:
            # Validate expense data
            await self._validate_expense_creation_data(expense_data, user_id)
            
            # Validate category belongs to user and is expense type
            await self._validate_user_category(user_id, expense_data.category_id)
            
            # Validate currency
            self._validate_currency(expense_data.currency)
            
            # Validate amount
            self._validate_amount(expense_data.total_amount)
            
            logger.info(f"Creating simple expense with payment_method: {expense_data.payment_method}")
            
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
            
            created_expense = await self.expense_repo.create(expense)
            logger.info(f"Simple expense created successfully: {created_expense.id} for user {user_id}")
            return created_expense
            
        except (
            ExpenseValidationError, InvalidAmountError, InvalidCurrencyError,
            CategoryNotFoundError, InvalidCategoryTypeError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating simple expense for user {user_id}: {str(e)}", exc_info=True)
            raise InternalServerError(
                detail="Failed to create simple expense due to internal error",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def create_invoice_expense(self, user_id: str, expense_data: InvoiceExpenseCreate) -> Expense:
        """Create an invoice expense with automatic tax calculation and validation."""
        try:
            # Validate invoice-specific requirements
            await self._validate_invoice_creation_data(expense_data, user_id)
            
            # Validate category belongs to user and is expense type
            await self._validate_user_category(user_id, expense_data.category_id)
            
            # Validate currency
            self._validate_currency(expense_data.currency)
            
            # Validate amount
            self._validate_amount(expense_data.base_amount)
            
            # Check for duplicate invoice number
            if expense_data.invoice_number:
                await self._check_duplicate_invoice_number(user_id, expense_data.invoice_number)
            
            # Business logic: Calculate tax if tax_config_id provided
            tax_amount = Decimal('0.00')
            
            if expense_data.tax_config_id:
                business_service = BusinessService(self.db)
                try:
                    tax_config = await business_service.get_tax_configuration(str(expense_data.tax_config_id), user_id)
                    if tax_config:
                        tax_amount = self._calculate_tax_amount(expense_data.base_amount, tax_config.rate)
                except Exception as e:
                    logger.warning(f"Could not get tax configuration: {str(e)}")
                    raise TaxConfigurationNotFoundError(
                        detail="Tax configuration not found or invalid",
                        context={"tax_config_id": str(expense_data.tax_config_id)}
                    )
            
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
            
            created_expense = await self.expense_repo.create(expense)
            logger.info(f"Invoice expense created successfully: {created_expense.id} for user {user_id}")
            return created_expense
            
        except (
            ExpenseValidationError, InvoiceRequiredFieldsError, InvalidAmountError,
            InvalidCurrencyError, DuplicateInvoiceNumberError, TaxConfigurationNotFoundError,
            CategoryNotFoundError, ContactNotFoundError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating invoice expense for user {user_id}: {str(e)}", exc_info=True)
            raise InternalServerError(
                detail="Failed to create invoice expense due to internal error",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_expense_by_id(self, user_id: str, expense_id: uuid.UUID) -> Expense:
        """Get expense by ID - raises exception if not found."""
        try:
            expense = await self.expense_repo.get_by_id(user_id, expense_id)
            if not expense:
                raise ExpenseNotFoundError(
                    detail=f"Expense with ID {expense_id} not found",
                    context={"expense_id": str(expense_id), "user_id": user_id}
                )
            return expense
        except ExpenseNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving expense {expense_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve expense",
                context={"expense_id": str(expense_id), "user_id": user_id, "original_error": str(e)}
            )

    async def update_expense(self, user_id: str, expense_id: uuid.UUID, expense_data: ExpenseUpdate) -> Expense:
        """Update expense with comprehensive validation and tax recalculation."""
        try:
            # Get existing expense
            expense = await self.get_expense_by_id(user_id, expense_id)
            
            # Business rule: Cannot modify paid invoices (except certain fields)
            if (expense.expense_type == ExpenseType.INVOICE and 
                expense.payment_status == PaymentStatus.PAID):
                
                update_data = expense_data.model_dump(exclude_unset=True)
                restricted_fields = {'base_amount', 'tax_amount', 'total_amount', 'contact_id', 'invoice_number'}
                
                if any(field in update_data for field in restricted_fields):
                    raise PaidInvoiceModificationError(
                        detail="Cannot modify financial details of paid invoices",
                        context={"expense_id": str(expense_id), "restricted_fields": list(restricted_fields)}
                    )
            
            # Validate update data
            update_data = expense_data.model_dump(exclude_unset=True)
            if not update_data:
                raise ExpenseValidationError(
                    detail="No valid fields provided for update",
                    context={"expense_id": str(expense_id), "user_id": user_id}
                )
            
            # Validate category if provided
            if 'category_id' in update_data:
                await self._validate_user_category(user_id, update_data['category_id'])
            
            # Validate currency if provided
            if 'currency' in update_data:
                self._validate_currency(update_data['currency'])
            
            # Validate amounts if provided
            if 'base_amount' in update_data:
                self._validate_amount(update_data['base_amount'])
            if 'total_amount' in update_data:
                self._validate_amount(update_data['total_amount'])
            
            # Check duplicate invoice number if being updated
            if ('invoice_number' in update_data and 
                update_data['invoice_number'] != expense.invoice_number):
                await self._check_duplicate_invoice_number(
                    user_id, update_data['invoice_number'], exclude_id=expense_id
                )
            
            # Business logic: Recalculate tax if base_amount or tax_config_id changed
            if ('base_amount' in update_data or 'tax_config_id' in update_data) and expense.expense_type == ExpenseType.INVOICE:
                base_amount = update_data.get('base_amount', expense.base_amount)
                tax_config_id = update_data.get('tax_config_id', expense.tax_config_id)
                
                if tax_config_id:
                    business_service = BusinessService(self.db)
                    try:
                        tax_config = await business_service.get_tax_configuration(str(tax_config_id), user_id)
                        if tax_config:
                            tax_amount = self._calculate_tax_amount(base_amount, tax_config.rate)
                            update_data['tax_amount'] = tax_amount
                            update_data['total_amount'] = base_amount + tax_amount
                    except Exception as e:
                        logger.warning(f"Could not recalculate tax: {str(e)}")
                        raise TaxConfigurationNotFoundError()
            
            # Apply updates
            for field, value in update_data.items():
                setattr(expense, field, value)
            
            updated_expense = await self.expense_repo.update(expense)
            logger.info(f"Expense updated successfully: {expense_id} for user {user_id}")
            return updated_expense
            
        except (
            ExpenseNotFoundError, ExpenseValidationError, PaidInvoiceModificationError,
            InvalidAmountError, InvalidCurrencyError, DuplicateInvoiceNumberError,
            TaxConfigurationNotFoundError, CategoryNotFoundError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating expense {expense_id}: {str(e)}", exc_info=True)
            raise ExpenseUpdateError(
                detail="Failed to update expense due to internal error",
                context={"expense_id": str(expense_id), "user_id": user_id, "original_error": str(e)}
            )

    async def delete_expense(self, user_id: str, expense_id: uuid.UUID) -> bool:
        """Soft delete expense with business rule validation."""
        try:
            # Get existing expense
            expense = await self.get_expense_by_id(user_id, expense_id)
            
            # Business rule: Warn about deleting paid invoices (but allow it)
            if (expense.payment_status == PaymentStatus.PAID and 
                expense.expense_type == ExpenseType.INVOICE):
                logger.warning(
                    f"Deleting paid invoice {expense_id} for user {user_id}. "
                    "This may affect financial records."
                )
            
            # Perform soft delete
            result = await self.expense_repo.delete(expense)
            logger.info(f"Expense deleted successfully: {expense_id} for user {user_id}")
            return result
            
        except ExpenseNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting expense {expense_id}: {str(e)}", exc_info=True)
            raise ExpenseDeleteError(
                detail="Failed to delete expense due to internal error",
                context={"expense_id": str(expense_id), "user_id": user_id, "original_error": str(e)}
            )

    async def mark_expense_as_paid(
        self, 
        user_id: str, 
        expense_id: uuid.UUID, 
        payment_date: Optional[datetime] = None
    ) -> Expense:
        """Mark expense as paid with validation."""
        try:
            expense = await self.get_expense_by_id(user_id, expense_id)
            
            # Business logic: Validate payment status transition
            if expense.payment_status == PaymentStatus.PAID:
                raise InvalidPaymentStatusError(
                    detail="Expense is already marked as paid",
                    context={"expense_id": str(expense_id), "current_status": expense.payment_status}
                )
            
            # Business logic: Set payment status and date
            expense.payment_status = PaymentStatus.PAID
            expense.payment_date = payment_date or datetime.utcnow()
            
            updated_expense = await self.expense_repo.update(expense)
            logger.info(f"Expense marked as paid: {expense_id} for user {user_id}")
            return updated_expense
            
        except (ExpenseNotFoundError, InvalidPaymentStatusError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error marking expense as paid {expense_id}: {str(e)}", exc_info=True)
            raise ExpenseUpdateError(
                detail="Failed to mark expense as paid due to internal error",
                context={"expense_id": str(expense_id), "user_id": user_id, "original_error": str(e)}
            )

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
        """Get expenses with advanced filtering and sorting with validation."""
        try:
            # Validate pagination parameters
            if skip < 0:
                raise ValidationError(
                    detail="Skip parameter cannot be negative",
                    context={"skip": skip}
                )
            if limit <= 0 or limit > 1000:
                raise ValidationError(
                    detail="Limit must be between 1 and 1000",
                    context={"limit": limit}
                )
            
            return await self.expense_repo.get_with_filters(
                user_id, filters, skip, limit, sort_by, sort_order
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting expenses with filters for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve expenses with filters",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_overdue_expenses(self, user_id: str) -> OverdueExpensesListResponse:
        """Get all overdue invoice expenses."""
        try:
            return await self.expense_repo.get_overdue_expenses(user_id)
        except Exception as e:
            logger.error(f"Error getting overdue expenses for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve overdue expenses",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_expenses_paginated(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "expense_date",
        sort_order: str = "desc"
    ) -> Tuple[List[Expense], int]:
        """Simple paginated expenses with validation."""
        try:
            # Validate pagination parameters
            if skip < 0:
                raise ValidationError(
                    detail="Skip parameter cannot be negative",
                    context={"skip": skip}
                )
            if limit <= 0 or limit > 1000:
                raise ValidationError(
                    detail="Limit must be between 1 and 1000",
                    context={"limit": limit}
                )
            
            return await self.expense_repo.get_paginated(
                user_id, skip, limit, sort_by, sort_order
            )
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting paginated expenses for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve expenses",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_expenses_by_type(
        self,
        user_id: str,
        expense_type: ExpenseType,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Expense], int]:
        """Get expenses by type (simple or invoice)"""
        try:
            # Validate pagination parameters
            if skip < 0:
                raise ValidationError(
                    detail="Skip parameter cannot be negative",
                    context={"skip": skip}
                )
            if limit <= 0 or limit > 1000:
                raise ValidationError(
                    detail="Limit must be between 1 and 1000",
                    context={"limit": limit}
                )
            
            # Validate expense type
            if not isinstance(expense_type, ExpenseType):
                raise InvalidExpenseTypeError(
                    detail=f"Invalid expense type: {expense_type}",
                    context={"expense_type": str(expense_type)}
                )
            # Delegate to repository for data access
            return await self.expense_repo.get_by_type(
                user_id, expense_type, skip, limit
            )
        
        except (ValidationError, InvalidExpenseTypeError):
            raise
        except Exception as e:
            logger.error(f"Error getting {expense_type} expenses for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail=f"Failed to retrieve {expense_type.value} expenses",
                context={"user_id": user_id, "expense_type": expense_type.value, "original_error": str(e)}
            )
       
    # Document Analysis & OCR Methods
    async def create_document_analysis(self, user_id: str, analysis_data: DocumentAnalysisCreate) -> DocumentAnalysis:
        """Create document analysis record for OCR processing with validation."""
        try:
            # Validate file type and size if provided
            if hasattr(analysis_data, 'file_type') and analysis_data.file_type:
                self._validate_file_type(analysis_data.file_type)
            
            if hasattr(analysis_data, 'file_size') and analysis_data.file_size:
                self._validate_file_size(analysis_data.file_size)
            
            # Create document analysis model
            analysis = DocumentAnalysis(
                id=uuid.uuid4(),
                user_id=user_id,
                **analysis_data.model_dump()
            )
            
            created_analysis = await self.expense_repo.create_document_analysis(analysis)
            logger.info(f"Document analysis created: {created_analysis.id} for user {user_id}")
            return created_analysis
            
        except (InvalidFileTypeError, FileSizeLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error creating document analysis for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to create document analysis",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def update_analysis_status(
        self,
        analysis_id: uuid.UUID,
        status: AnalysisStatus,
        extracted_data: Optional[Dict[str, Any]] = None,
        confidence_score: Optional[Decimal] = None,
        error_message: Optional[str] = None
    ) -> DocumentAnalysis:
        """Update document analysis status and results with validation."""
        try:
            # Get analysis from repository
            analysis = await self.expense_repo.get_document_analysis_by_id(analysis_id)
            if not analysis:
                raise DocumentAnalysisNotFoundError(
                    detail=f"Document analysis with ID {analysis_id} not found",
                    context={"analysis_id": str(analysis_id)}
                )
            
            # Validate confidence score if provided
            if confidence_score is not None:
                if confidence_score < 0 or confidence_score > 1:
                    raise ExpenseValidationError(
                        detail="Confidence score must be between 0 and 1",
                        context={"confidence_score": float(confidence_score)}
                    )
            
            # Business logic: Update analysis status and fields
            analysis.analysis_status = status
            if extracted_data:
                analysis.extracted_data = extracted_data
            if confidence_score is not None:
                analysis.confidence_score = confidence_score
            if error_message:
                analysis.error_message = error_message
            
            # Business logic: Set processing timestamps
            now = datetime.utcnow()
            if status == AnalysisStatus.PROCESSING:
                analysis.processing_started_at = now
            elif status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                analysis.processing_completed_at = now
            
            updated_analysis = await self.expense_repo.update_document_analysis(analysis)
            logger.info(f"Analysis status updated: {analysis_id} to {status}")
            return updated_analysis
            
        except (DocumentAnalysisNotFoundError, ExpenseValidationError):
            raise
        except Exception as e:
            logger.error(f"Error updating analysis status for {analysis_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to update document analysis status",
                context={"analysis_id": str(analysis_id), "original_error": str(e)}
            )

    async def create_expense_from_analysis(
        self,
        user_id: str,
        analysis_id: uuid.UUID,
        user_corrections: Optional[Dict[str, Any]] = None
    ) -> Expense:
        """Create expense from OCR analysis results with comprehensive validation."""
        try:
            # Get analysis from repository
            analysis = await self.expense_repo.get_document_analysis_by_id(analysis_id)
            
            if not analysis or not analysis.extracted_data:
                raise ExpenseValidationError(
                    detail="Analysis not found or no extracted data available",
                    context={"analysis_id": str(analysis_id)}
                )
            
            extracted = analysis.extracted_data.copy()
            
            # Apply user corrections
            if user_corrections:
                extracted.update(user_corrections)
            
            # Validate required fields
            if not extracted.get('category_id'):
                raise ExpenseValidationError(
                    detail="Category ID is required for expense creation",
                    context={"analysis_id": str(analysis_id)}
                )
            
            # Determine expense type based on extracted data
            expense_type = ExpenseType.INVOICE if extracted.get('invoice_number') else ExpenseType.SIMPLE
            
            # Create expense based on type
            if expense_type == ExpenseType.INVOICE:
                # Validate invoice requirements
                if not extracted.get('contact_id'):
                    raise InvoiceRequiredFieldsError(
                        detail="Invoice expenses require a contact_id",
                        context={"analysis_id": str(analysis_id)}
                    )
                
                # Get or create default tax config
                tax_config_id = None
                if extracted.get('tax_config_id'):
                    tax_config_id = uuid.UUID(str(extracted['tax_config_id']))
                else:
                    # Try to find default tax config
                    try:
                        business_service = BusinessService(self.db)
                        tax_configs = await business_service.get_tax_configurations(user_id, active_only=True)
                        tax_config = next((tc for tc in tax_configs if tc.is_default), None)
                        tax_config_id = tax_config.id if tax_config else None
                    except Exception as e:
                        logger.warning(f"Could not get default tax config: {str(e)}")
                
                expense_data = InvoiceExpenseCreate(
                    description=extracted.get('description', 'Imported from document'),
                    expense_date=self._parse_date(extracted.get('expense_date')) or datetime.utcnow(),
                    contact_id=uuid.UUID(str(extracted['contact_id'])),
                    invoice_number=extracted.get('invoice_number'),
                    base_amount=self._parse_amount(extracted.get('base_amount', 0)),
                    tax_config_id=tax_config_id,
                    category_id=uuid.UUID(str(extracted['category_id'])),
                    payment_due_date=self._parse_date(extracted.get('payment_due_date')),
                    currency=extracted.get('currency', 'USD'),
                    payment_method=self._parse_payment_method(extracted.get('payment_method'))
                )
                expense = await self.create_invoice_expense(user_id, expense_data)
            else:
                expense_data = SimpleExpenseCreate(
                    description=extracted.get('description', 'Imported from document'),
                    expense_date=self._parse_date(extracted.get('expense_date')) or datetime.utcnow(),
                    total_amount=self._parse_amount(extracted.get('total_amount', 0)),
                    payment_method=self._parse_payment_method(extracted.get('payment_method')),
                    category_id=uuid.UUID(str(extracted['category_id'])),
                    currency=extracted.get('currency', 'USD')
                )
                expense = await self.create_simple_expense(user_id, expense_data)
            
            # Link analysis to expense
            analysis.expense_id = expense.id
            await self.expense_repo.update_document_analysis(analysis)
            
            logger.info(f"Created expense {expense.id} from analysis {analysis_id}")
            return expense
            
        except (
            ExpenseValidationError, InvoiceRequiredFieldsError, InvalidAmountError,
            InvalidCurrencyError, CategoryNotFoundError, ContactNotFoundError
        ):
            raise
        except Exception as e:
            logger.error(f"Error creating expense from analysis {analysis_id}: {str(e)}", exc_info=True)
            raise ExpenseImportError(
                detail="Failed to create expense from document analysis",
                context={"analysis_id": str(analysis_id), "user_id": user_id, "original_error": str(e)}
            )

    # Analytics & Reporting
    async def get_expense_stats(self, user_id: str) -> ExpenseStats:
        """Get comprehensive expense statistics."""
        try:
            return await self.expense_repo.get_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting expense stats for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve expense statistics",
                context={"user_id": user_id, "original_error": str(e)}
            )

    # File Management
    async def add_attachment(self, user_id: str, expense_id: uuid.UUID, attachment_data: AttachmentCreate) -> ExpenseAttachment:
        """Add file attachment to expense with validation."""
        try:
            # Verify expense belongs to user
            expense = await self.get_expense_by_id(user_id, expense_id)
            
            # Validate file if data provided
            if hasattr(attachment_data, 'file_type') and attachment_data.file_type:
                self._validate_file_type(attachment_data.file_type)
            
            if hasattr(attachment_data, 'file_size') and attachment_data.file_size:
                self._validate_file_size(attachment_data.file_size)
            
            # Create attachment model
            attachment = ExpenseAttachment(
                id=uuid.uuid4(),
                expense_id=expense_id,
                **attachment_data.model_dump()
            )
            
            created_attachment = await self.expense_repo.create_attachment(attachment)
            logger.info(f"Attachment added to expense {expense_id}: {created_attachment.id}")
            return created_attachment
            
        except (ExpenseNotFoundError, InvalidFileTypeError, FileSizeLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error adding attachment to expense {expense_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to add attachment to expense",
                context={"expense_id": str(expense_id), "user_id": user_id, "original_error": str(e)}
            )

    # Helper Methods
    async def _validate_expense_creation_data(self, expense_data, user_id: str) -> None:
        """Validate basic expense creation data."""
        if not expense_data.description or not expense_data.description.strip():
            raise ExpenseValidationError(
                detail="Expense description cannot be empty",
                context={"description": expense_data.description}
            )
        
        if len(expense_data.description.strip()) > 500:
            raise ExpenseValidationError(
                detail="Expense description must be 500 characters or less",
                context={"description": expense_data.description, "length": len(expense_data.description)}
            )
        
        # Validate expense date is not too far in the future
        if expense_data.expense_date > datetime.now() + timedelta(days=30):
            raise ExpenseValidationError(
                detail="Expense date cannot be more than 30 days in the future",
                context={"expense_date": expense_data.expense_date}
            )

    async def _validate_invoice_creation_data(self, expense_data: InvoiceExpenseCreate, user_id: str) -> None:
        """Validate invoice-specific creation data."""
        await self._validate_expense_creation_data(expense_data, user_id)
        
        # Validate contact exists if provided
        if expense_data.contact_id:
            # This would typically validate with ContactService
            # For now, just ensure it's a valid UUID format
            try:
                uuid.UUID(str(expense_data.contact_id))
            except ValueError:
                raise ContactNotFoundError(
                    detail="Invalid contact ID format",
                    context={"contact_id": str(expense_data.contact_id)}
                )

    def _validate_currency(self, currency: str) -> None:
        """Validate currency code."""
        if not currency or currency not in SUPPORTED_CURRENCIES:
            raise InvalidCurrencyError(
                detail=f"Currency must be one of: {', '.join(SUPPORTED_CURRENCIES)}",
                context={"currency": currency, "supported": SUPPORTED_CURRENCIES}
            )

    def _validate_amount(self, amount: Decimal) -> None:
        """Validate monetary amount."""
        if amount is None:
            raise InvalidAmountError(
                detail="Amount cannot be null",
                context={"amount": amount}
            )
        
        if amount <= 0:
            raise InvalidAmountError(
                detail="Amount must be positive",
                context={"amount": float(amount)}
            )
        
        if amount > Decimal('999999.99'):
            raise InvalidAmountError(
                detail="Amount exceeds maximum allowed value",
                context={"amount": float(amount), "max_allowed": 999999.99}
            )

    async def _validate_user_category(self, user_id: str, category_id: uuid.UUID) -> Category:
        """Validate that category belongs to user and is expense type."""
        try:
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
                raise CategoryNotFoundError(
                    detail="Category not found or is not an active expense category",
                    context={"category_id": str(category_id), "user_id": user_id}
                )
            
            return category
        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error validating category: {str(e)}")
            raise InternalServerError(
                detail="Failed to validate category",
                context={"category_id": str(category_id), "original_error": str(e)}
            )

    def _calculate_tax_amount(self, base_amount: Decimal, tax_rate: Decimal) -> Decimal:
        """Calculate tax amount with proper rounding and validation."""
        try:
            if tax_rate < 0 or tax_rate > 100:
                raise InvalidTaxCalculationError(
                    detail="Tax rate must be between 0 and 100",
                    context={"tax_rate": float(tax_rate)}
                )
            
            return (base_amount * tax_rate / 100).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError) as e:
            raise InvalidTaxCalculationError(
                detail="Invalid tax calculation parameters",
                context={"base_amount": float(base_amount), "tax_rate": float(tax_rate), "error": str(e)}
            )

    async def _check_duplicate_invoice_number(
        self, 
        user_id: str, 
        invoice_number: str, 
        exclude_id: Optional[uuid.UUID] = None
    ) -> None:
        """Check for duplicate invoice numbers."""
        try:
            if not invoice_number or not invoice_number.strip():
                return  # Empty invoice numbers are allowed
                
            duplicate_exists = await self.expense_repo.check_duplicate_invoice_number(
                user_id, invoice_number.strip(), exclude_id
            )
            
            if duplicate_exists:
                raise DuplicateInvoiceNumberError(
                    detail=f"Invoice number '{invoice_number}' already exists",
                    context={"invoice_number": invoice_number, "user_id": user_id}
                )
        except DuplicateInvoiceNumberError:
            raise
        except Exception as e:
            logger.error(f"Error checking duplicate invoice number: {str(e)}")
            raise InternalServerError(
                detail="Failed to validate invoice number uniqueness",
                context={"invoice_number": invoice_number, "original_error": str(e)}
            )
        
    # Private validation helper methods
    def _validate_file_type(self, file_type: str) -> None:
        """Validate uploaded file type."""
        if file_type not in SUPPORTED_FILE_TYPES:
            raise InvalidFileTypeError(
                detail=f"File type '{file_type}' not supported. Supported types: {', '.join(SUPPORTED_FILE_TYPES)}",
                context={"file_type": file_type, "supported_types": SUPPORTED_FILE_TYPES}
            )

    def _validate_file_size(self, file_size: int) -> None:
        """Validate uploaded file size."""
        max_size = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
        if file_size > max_size:
            raise FileSizeLimitExceededError(
                detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)",
                context={"file_size": file_size, "max_size_mb": MAX_FILE_SIZE_MB}
            )

    def _parse_amount(self, amount_value: Any) -> Decimal:
        """Parse amount from various formats."""
        try:
            if amount_value is None:
                return Decimal('0.00')
            
            if isinstance(amount_value, str):
                # Remove currency symbols and whitespace
                cleaned = re.sub(r'[^\d.-]', '', amount_value.strip())
                return Decimal(cleaned) if cleaned else Decimal('0.00')
            
            return Decimal(str(amount_value))
        except (ValueError, InvalidOperation):
            logger.warning(f"Could not parse amount: {amount_value}")
            return Decimal('0.00')

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats."""
        if date_value is None:
            return None
        
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Try common date formats
            date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
        
        logger.warning(f"Could not parse date: {date_value}")
        return None

    def _parse_payment_method(self, payment_method_value: Any) -> PaymentMethod:
        """Parse payment method from string."""
        if payment_method_value is None:
            return PaymentMethod.CARD  # Default
        
        try:
            if isinstance(payment_method_value, str):
                # Try to match enum values
                method_upper = payment_method_value.upper()
                for method in PaymentMethod:
                    if method.value.upper() == method_upper:
                        return method
            
            return PaymentMethod(payment_method_value)
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse payment method: {payment_method_value}")
            return PaymentMethod.CARD  # Default