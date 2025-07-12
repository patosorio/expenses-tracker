from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func, extract, desc, asc, case
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import json
import logging

from src.expenses.models import (
    Expense, DocumentAnalysis, ExpenseAttachment,
    ExpenseType, PaymentMethod, PaymentStatus, AnalysisStatus
)
from src.business.models import TaxConfiguration
from src.expenses.schemas import (
    SimpleExpenseCreate, InvoiceExpenseCreate, ExpenseUpdate,
    TaxConfigCreate, TaxConfigUpdate, AttachmentCreate, DocumentAnalysisCreate,
    ExpenseFilter, ExpenseSummary, ExpenseStats, ExpensePreviewResponse,
    OverdueExpensesListResponse, OverdueExpenseResponse
)
from src.categories.models import Category, CategoryType
from src.users.models import User
from src.database import get_db
from src.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ExpenseService:
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    # Core CRUD Operations
    async def create_simple_expense(self, user_id: str, expense_data: SimpleExpenseCreate) -> Expense:
        """Create a simple (receipt) expense with automatic payment date setting"""
        try:
            # Validate category belongs to user and is expense type
            category = await self._validate_user_category(user_id, expense_data.category_id)
            
            # For simple expenses: base_amount = total_amount, tax_amount = 0, payment_date = expense_date
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
                payment_status=PaymentStatus.PAID,  # Simple expenses are paid immediately
                payment_date=expense_data.expense_date,  # Auto-set to expense date
                base_amount=expense_data.total_amount,
                tax_amount=Decimal('0.00'),
                total_amount=expense_data.total_amount,
                currency=expense_data.currency,
                tags=expense_data.tags,
                custom_fields=expense_data.custom_fields
            )
            
            self.db.add(expense)
            self.db.commit()
            self.db.refresh(expense)
            
            logger.info(f"Created simple expense {expense.id} for user {user_id}")
            return expense
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating simple expense for user {user_id}: {str(e)}")
            raise ValidationError(f"Failed to create expense: {str(e)}")

    async def create_invoice_expense(self, user_id: str, expense_data: InvoiceExpenseCreate) -> Expense:
        """Create an invoice expense with automatic tax calculation"""
        try:
            # Validate category belongs to user and is expense type
            category = await self._validate_user_category(user_id, expense_data.category_id)
            
            # Calculate tax if tax_config_id provided
            tax_amount = Decimal('0.00')
            tax_config = None
            
            if expense_data.tax_config_id:
                tax_config = await self.get_user_tax_config(user_id, expense_data.tax_config_id)
                if tax_config:
                    tax_amount = self._calculate_tax_amount(expense_data.base_amount, tax_config.tax_rate)
            
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
                payment_status=PaymentStatus.PENDING,  # Invoices start as pending
                payment_date=None,  # Not paid yet
                invoice_number=expense_data.invoice_number,
                supplier_name=expense_data.supplier_name,
                supplier_tax_id=expense_data.supplier_tax_id,
                payment_due_date=expense_data.payment_due_date,
                base_amount=expense_data.base_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                currency=expense_data.currency,
                tax_config_id=expense_data.tax_config_id,
                tags=expense_data.tags,
                custom_fields=expense_data.custom_fields
            )
            
            self.db.add(expense)
            self.db.commit()
            self.db.refresh(expense)
            
            logger.info(f"Created invoice expense {expense.id} for user {user_id}")
            return expense
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating invoice expense for user {user_id}: {str(e)}")
            raise ValidationError(f"Failed to create invoice expense: {str(e)}")

    async def get_expense_by_id(self, user_id: str, expense_id: uuid.UUID) -> Optional[Expense]:
        """Get expense by ID with full relationships"""
        expense = (
            self.db.query(Expense)
            .options(
                selectinload(Expense.attachments),
                selectinload(Expense.document_analysis),
                selectinload(Expense.category),
                selectinload(Expense.tax_config)
            )
            .filter(and_(Expense.id == expense_id, Expense.user_id == user_id, Expense.is_active == True))
            .first()
        )
        
        if not expense:
            logger.warning(f"Expense {expense_id} not found for user {user_id}")
            return None
            
        return expense

    async def update_expense(self, user_id: str, expense_id: uuid.UUID, expense_data: ExpenseUpdate) -> Expense:
        """Update expense with tax recalculation if needed"""
        try:
            expense = await self.get_expense_by_id(user_id, expense_id)
            if not expense:
                raise NotFoundError("Expense not found")
            
            # Update fields
            update_data = expense_data.model_dump(exclude_unset=True)
            
            # Validate category if provided
            if expense_data.category_id:
                await self._validate_user_category(user_id, expense_data.category_id)
            
            # Recalculate tax if base_amount or tax_config_id changed
            if 'base_amount' in update_data or 'tax_config_id' in update_data:
                base_amount = update_data.get('base_amount', expense.base_amount)
                tax_config_id = update_data.get('tax_config_id', expense.tax_config_id)
                
                if tax_config_id and expense.expense_type == ExpenseType.INVOICE:
                    tax_config = await self.get_user_tax_config(user_id, tax_config_id)
                    if tax_config:
                        tax_amount = self._calculate_tax_amount(base_amount, tax_config.tax_rate)
                        update_data['tax_amount'] = tax_amount
                        update_data['total_amount'] = base_amount + tax_amount
                
            # Apply updates
            for field, value in update_data.items():
                setattr(expense, field, value)
            
            expense.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(expense)
            
            logger.info(f"Updated expense {expense_id} for user {user_id}")
            return expense
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating expense {expense_id} for user {user_id}: {str(e)}")
            raise

    async def delete_expense(self, user_id: str, expense_id: uuid.UUID) -> bool:
        """Soft delete expense with attachment cleanup"""
        try:
            expense = await self.get_expense_by_id(user_id, expense_id)
            if not expense:
                raise NotFoundError("Expense not found")
            
            # Soft delete
            expense.is_active = False
            expense.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Deleted expense {expense_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting expense {expense_id} for user {user_id}: {str(e)}")
            raise

    async def mark_expense_as_paid(self, user_id: str, expense_id: uuid.UUID, payment_date: Optional[datetime] = None) -> Expense:
        """Mark expense as paid and set payment date"""
        try:
            expense = await self.get_expense_by_id(user_id, expense_id)
            if not expense:
                raise NotFoundError("Expense not found")
            
            expense.payment_status = PaymentStatus.PAID
            expense.payment_date = payment_date or datetime.utcnow()
            expense.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(expense)
            
            logger.info(f"Marked expense {expense_id} as paid for user {user_id}")
            return expense
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking expense {expense_id} as paid for user {user_id}: {str(e)}")
            raise

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
            query = (
                self.db.query(Expense)
                .filter(and_(Expense.user_id == user_id, Expense.is_active == True))
            )
            
            # Apply filters
            if filters.expense_type:
                query = query.filter(Expense.expense_type == filters.expense_type)
            
            if filters.payment_status:
                query = query.filter(Expense.payment_status == filters.payment_status)
            
            if filters.payment_method:
                query = query.filter(Expense.payment_method == filters.payment_method)
            
            if filters.category_id:
                query = query.filter(Expense.category_id == filters.category_id)
            
            if filters.supplier_name:
                query = query.filter(Expense.supplier_name.ilike(f"%{filters.supplier_name}%"))
            
            if filters.min_amount:
                query = query.filter(Expense.total_amount >= filters.min_amount)
            
            if filters.max_amount:
                query = query.filter(Expense.total_amount <= filters.max_amount)
            
            if filters.date_from:
                query = query.filter(Expense.expense_date >= filters.date_from)
            
            if filters.date_to:
                query = query.filter(Expense.expense_date <= filters.date_to)
            
            if filters.overdue_only:
                query = query.filter(
                    and_(
                        Expense.expense_type == ExpenseType.INVOICE,
                        Expense.payment_status != PaymentStatus.PAID,
                        Expense.payment_due_date < datetime.utcnow()
                    )
                )
            
            if filters.tags:
                # JSON contains any of the specified tags
                tag_conditions = [func.json_extract_path_text(Expense.tags, str(i)).in_(filters.tags) for i in range(10)]
                query = query.filter(or_(*tag_conditions))
            
            if filters.search:
                search_pattern = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Expense.description.ilike(search_pattern),
                        Expense.supplier_name.ilike(search_pattern),
                        Expense.invoice_number.ilike(search_pattern),
                        Expense.notes.ilike(search_pattern)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            sort_column = getattr(Expense, sort_by, Expense.expense_date)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Apply pagination
            expenses = query.offset(skip).limit(limit).all()
            
            return expenses, total
            
        except Exception as e:
            logger.error(f"Error getting expenses with filters for user {user_id}: {str(e)}")
            raise

    async def get_overdue_expenses(self, user_id: str) -> OverdueExpensesListResponse:
        """Get all overdue invoice expenses"""
        try:
            overdue_expenses = (
                self.db.query(Expense)
                .filter(
                    and_(
                        Expense.user_id == user_id,
                        Expense.expense_type == ExpenseType.INVOICE,
                        Expense.payment_status != PaymentStatus.PAID,
                        Expense.payment_due_date < datetime.utcnow(),
                        Expense.is_active == True
                    )
                )
                .order_by(desc(Expense.payment_due_date))
                .all()
            )
            
            overdue_list = []
            total_overdue_amount = Decimal('0.00')
            
            for expense in overdue_expenses:
                overdue_item = OverdueExpenseResponse(
                    id=expense.id,
                    description=expense.description,
                    supplier_name=expense.supplier_name,
                    invoice_number=expense.invoice_number,
                    total_amount=expense.total_amount,
                    payment_due_date=expense.payment_due_date,
                    days_overdue=expense.days_overdue,
                    currency=expense.currency
                )
                overdue_list.append(overdue_item)
                total_overdue_amount += expense.total_amount
            
            return OverdueExpensesListResponse(
                overdue_invoices=overdue_list,
                total_overdue_amount=total_overdue_amount,
                count=len(overdue_list),
                currency=overdue_expenses[0].currency if overdue_expenses else 'EUR'
            )
            
        except Exception as e:
            logger.error(f"Error getting overdue expenses for user {user_id}: {str(e)}")
            raise

    # Tax Management
    async def create_tax_config(self, user_id: str, tax_data: TaxConfigCreate) -> TaxConfiguration:
        """Create tax configuration for user"""
        try:
            # If setting as default, unset other defaults
            if tax_data.is_default:
                await self._unset_default_tax_configs(user_id)
            
            tax_config = TaxConfiguration(
                id=uuid.uuid4(),
                user_id=user_id,
                **tax_data.model_dump()
            )
            
            self.db.add(tax_config)
            self.db.commit()
            self.db.refresh(tax_config)
            
            logger.info(f"Created tax config {tax_config.id} for user {user_id}")
            return tax_config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating tax config for user {user_id}: {str(e)}")
            raise

    async def get_user_tax_configs(self, user_id: str) -> List[TaxConfiguration]:
        """Get all active tax configurations for user"""
        return (
            self.db.query(TaxConfiguration)
            .filter(and_(TaxConfiguration.user_id == user_id, TaxConfiguration.is_active == True))
            .order_by(desc(TaxConfiguration.is_default), TaxConfiguration.tax_name)
            .all()
        )

    async def get_user_tax_config(self, user_id: str, tax_config_id: uuid.UUID) -> Optional[TaxConfiguration]:
        """Get specific tax configuration"""
        return (
            self.db.query(TaxConfiguration)
            .filter(
                and_(
                    TaxConfiguration.id == tax_config_id,
                    TaxConfiguration.user_id == user_id,
                    TaxConfiguration.is_active == True
                )
            )
            .first()
        )

    async def get_default_tax_config(self, user_id: str) -> Optional[TaxConfiguration]:
        """Get user's default tax configuration"""
        return (
            self.db.query(TaxConfiguration)
            .filter(
                and_(
                    TaxConfiguration.user_id == user_id,
                    TaxConfiguration.is_default == True,
                    TaxConfiguration.is_active == True
                )
            )
            .first()
        )

    # Document Analysis & OCR
    async def create_document_analysis(self, user_id: str, analysis_data: DocumentAnalysisCreate) -> DocumentAnalysis:
        """Create document analysis record for OCR processing"""
        try:
            analysis = DocumentAnalysis(
                id=uuid.uuid4(),
                user_id=user_id,
                **analysis_data.model_dump()
            )
            
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            
            logger.info(f"Created document analysis {analysis.id} for user {user_id}")
            return analysis
            
        except Exception as e:
            self.db.rollback()
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
            analysis = self.db.query(DocumentAnalysis).filter(DocumentAnalysis.id == analysis_id).first()
            if not analysis:
                raise NotFoundError("Document analysis not found")
            
            analysis.analysis_status = status
            if extracted_data:
                analysis.extracted_data = extracted_data
            if confidence_score is not None:
                analysis.confidence_score = confidence_score
            if error_message:
                analysis.error_message = error_message
            
            if status == AnalysisStatus.PROCESSING:
                analysis.processing_started_at = datetime.utcnow()
            elif status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                analysis.processing_completed_at = datetime.utcnow()
            
            analysis.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(analysis)
            
            return analysis
            
        except Exception as e:
            self.db.rollback()
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
            analysis = (
                self.db.query(DocumentAnalysis)
                .filter(and_(DocumentAnalysis.id == analysis_id, DocumentAnalysis.user_id == user_id))
                .first()
            )
            
            if not analysis or not analysis.extracted_data:
                raise ValidationError("Analysis not found or no extracted data available")
            
            extracted = analysis.extracted_data
            
            # Apply user corrections
            if user_corrections:
                extracted.update(user_corrections)
            
            # Determine expense type based on extracted data
            expense_type = ExpenseType.INVOICE if extracted.get('invoice_number') or extracted.get('supplier_name') else ExpenseType.SIMPLE
            
            # Create expense based on type
            if expense_type == ExpenseType.INVOICE:
                # Find or create default tax config for tax calculation
                tax_config = await self.get_default_tax_config(user_id)
                tax_config_id = tax_config.id if tax_config else None
                
                expense_data = InvoiceExpenseCreate(
                    description=extracted.get('description', 'Imported from document'),
                    expense_date=extracted.get('expense_date', datetime.utcnow()),
                    supplier_name=extracted.get('supplier_name', 'Unknown Supplier'),
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
            
            # Link analysis to expense
            analysis.expense_id = expense.id
            self.db.commit()
            
            logger.info(f"Created expense {expense.id} from analysis {analysis_id}")
            return expense
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating expense from analysis {analysis_id}: {str(e)}")
            raise

    # Analytics & Reporting
    async def get_expense_stats(self, user_id: str) -> ExpenseStats:
        """Get comprehensive expense statistics"""
        try:
            # Basic aggregations
            total_result = (
                self.db.query(
                    func.sum(Expense.total_amount).label('total'),
                    func.count(Expense.id).label('count')
                )
                .filter(and_(Expense.user_id == user_id, Expense.is_active == True))
                .first()
            )
            
            total_expenses = total_result.total or Decimal('0.00')
            total_count = total_result.count or 0
            
            # Pending payments
            pending_result = (
                self.db.query(func.sum(Expense.total_amount))
                .filter(
                    and_(
                        Expense.user_id == user_id,
                        Expense.payment_status == PaymentStatus.PENDING,
                        Expense.is_active == True
                    )
                )
                .scalar()
            )
            pending_payments = pending_result or Decimal('0.00')
            
            # Overdue expenses
            overdue_result = (
                self.db.query(
                    func.count(Expense.id).label('count'),
                    func.sum(Expense.total_amount).label('amount')
                )
                .filter(
                    and_(
                        Expense.user_id == user_id,
                        Expense.expense_type == ExpenseType.INVOICE,
                        Expense.payment_status != PaymentStatus.PAID,
                        Expense.payment_due_date < datetime.utcnow(),
                        Expense.is_active == True
                    )
                )
                .first()
            )
            
            overdue_count = overdue_result.count or 0
            overdue_amount = overdue_result.amount or Decimal('0.00')
            
            # Monthly comparison
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            
            this_month_total = (
                self.db.query(func.sum(Expense.total_amount))
                .filter(
                    and_(
                        Expense.user_id == user_id,
                        Expense.expense_date >= current_month_start,
                        Expense.is_active == True
                    )
                )
                .scalar() or Decimal('0.00')
            )
            
            last_month_total = (
                self.db.query(func.sum(Expense.total_amount))
                .filter(
                    and_(
                        Expense.user_id == user_id,
                        Expense.expense_date >= last_month_start,
                        Expense.expense_date < current_month_start,
                        Expense.is_active == True
                    )
                )
                .scalar() or Decimal('0.00')
            )
            
            # Calculate monthly change percentage
            monthly_change_percent = Decimal('0.00')
            if last_month_total > 0:
                monthly_change_percent = ((this_month_total - last_month_total) / last_month_total * 100).quantize(Decimal('0.01'))
            
            # Top categories and suppliers (placeholder - would need joins)
            top_categories = []
            top_suppliers = []
            
            return ExpenseStats(
                total_expenses=total_expenses,
                total_count=total_count,
                pending_payments=pending_payments,
                overdue_count=overdue_count,
                overdue_amount=overdue_amount,
                this_month_total=this_month_total,
                last_month_total=last_month_total,
                monthly_change_percent=monthly_change_percent,
                top_categories=top_categories,
                top_suppliers=top_suppliers
            )
            
        except Exception as e:
            logger.error(f"Error getting expense stats for user {user_id}: {str(e)}")
            raise

    # File Management
    async def add_attachment(self, user_id: str, expense_id: uuid.UUID, attachment_data: AttachmentCreate) -> ExpenseAttachment:
        """Add file attachment to expense"""
        try:
            # Verify expense belongs to user
            expense = await self.get_expense_by_id(user_id, expense_id)
            if not expense:
                raise NotFoundError("Expense not found")
            
            attachment = ExpenseAttachment(
                id=uuid.uuid4(),
                expense_id=expense_id,
                **attachment_data.model_dump()
            )
            
            self.db.add(attachment)
            self.db.commit()
            self.db.refresh(attachment)
            
            logger.info(f"Added attachment {attachment.id} to expense {expense_id}")
            return attachment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding attachment to expense {expense_id}: {str(e)}")
            raise

    # Helper Methods
    async def _validate_user_category(self, user_id: str, category_id: uuid.UUID) -> Category:
        """Validate that category belongs to user and is expense type"""
        category = (
            self.db.query(Category)
            .filter(
                and_(
                    Category.id == category_id,
                    Category.user_id == user_id,
                    Category.type == CategoryType.EXPENSE,
                    Category.is_active == True
                )
            )
            .first()
        )
        
        if not category:
            raise ValidationError("Invalid category: must be an active expense category belonging to the user")
        
        return category

    def _calculate_tax_amount(self, base_amount: Decimal, tax_rate: Decimal) -> Decimal:
        """Calculate tax amount with proper rounding"""
        return (base_amount * tax_rate / 100).quantize(Decimal('0.01'))

    async def _unset_default_tax_configs(self, user_id: str) -> None:
        """Unset all default tax configurations for user"""
        self.db.query(TaxConfiguration).filter(
            and_(TaxConfiguration.user_id == user_id, TaxConfiguration.is_default == True)
        ).update({'is_default': False})
        self.db.commit()
