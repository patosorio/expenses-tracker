from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid
import logging

from .models import Expense, ExpenseType, PaymentStatus
from .repository import ExpenseRepository
from .schemas import SimpleExpenseCreate, InvoiceExpenseCreate, ExpenseStats, OverdueExpensesListResponse
from .exceptions import (
    # ✅ CORRECT - Using your actual exceptions
    ExpenseNotFoundError, ExpenseValidationError, ExpenseAlreadyExistsError,
    InvalidExpenseTypeError, InvalidPaymentStatusError, PaidInvoiceModificationError,
    DuplicateInvoiceNumberError, InvalidAmountError, InvalidTaxCalculationError,
    CategoryNotFoundError, InvalidCategoryTypeError, InvalidCurrencyError
)
from ..core.shared.base_service import BaseService
from ..core.shared.exceptions import ValidationError, InternalServerError

logger = logging.getLogger(__name__)

# Business constants  
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD"]
MAX_EXPENSE_AMOUNT = Decimal('1000000.00')
MIN_EXPENSE_AMOUNT = Decimal('0.01')


class ExpenseService(BaseService[Expense, ExpenseRepository]):
    """Expense service with business logic extending BaseService."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, ExpenseRepository, Expense)

    # Expense-specific business methods
    async def create_simple_expense(
        self, 
        user_id: str, 
        expense_data: SimpleExpenseCreate
    ) -> Expense:
        """Create a simple (receipt) expense with business validation."""
        try:
            data = expense_data.model_dump()
            data['expense_type'] = ExpenseType.SIMPLE
            data['payment_status'] = PaymentStatus.PAID
            
            return await self.create(data, user_id)
            
        except (ExpenseValidationError, InvalidAmountError, InvalidCurrencyError):
            raise
        except Exception as e:
            logger.error(f"Error creating simple expense for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to create simple expense",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def create_invoice_expense(
        self, 
        user_id: str, 
        expense_data: InvoiceExpenseCreate
    ) -> Expense:
        """Create an invoice expense with tax calculations."""
        try:
            data = expense_data.model_dump()
            data['expense_type'] = ExpenseType.INVOICE
            data['payment_status'] = PaymentStatus.PENDING
            
            # Calculate tax if needed
            if data.get('tax_rate') and data.get('base_amount'):
                try:
                    data['tax_amount'] = self._calculate_tax_amount(
                        data['base_amount'], 
                        data['tax_rate']
                    )
                    data['total_amount'] = data['base_amount'] + data['tax_amount']
                except Exception:
                    raise InvalidTaxCalculationError(
                        detail="Failed to calculate tax amount",
                        context={"base_amount": data['base_amount'], "tax_rate": data['tax_rate']}
                    )
            
            return await self.create(data, user_id)
            
        except (ExpenseValidationError, InvalidAmountError, InvalidTaxCalculationError, InvalidCurrencyError):
            raise
        except Exception as e:
            logger.error(f"Error creating invoice expense for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to create invoice expense",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def mark_as_paid(self, expense_id: uuid.UUID, user_id: str, payment_date: datetime = None) -> Expense:
        """Mark an invoice as paid."""
        try:
            expense = await self.get_by_id_or_raise(expense_id, user_id)
            
            if expense.expense_type != ExpenseType.INVOICE:
                raise InvalidExpenseTypeError(
                    detail="Only invoices can be marked as paid",
                    context={"expense_id": str(expense_id), "expense_type": expense.expense_type}
                )
            
            if expense.payment_status == PaymentStatus.PAID:
                raise InvalidPaymentStatusError(  # ✅ CORRECT exception
                    detail="Expense is already marked as paid",
                    context={"expense_id": str(expense_id)}
                )
            
            update_data = {
                'payment_status': PaymentStatus.PAID,
                'payment_date': payment_date or datetime.utcnow()
            }
            
            return await self.update(expense_id, update_data, user_id)
            
        except (ExpenseNotFoundError, InvalidExpenseTypeError, InvalidPaymentStatusError):
            raise
        except Exception as e:
            logger.error(f"Error marking expense as paid {expense_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to mark expense as paid",
                context={"expense_id": str(expense_id), "user_id": user_id}
            )

    async def get_expense_stats(self, user_id: str) -> ExpenseStats:
        """Get expense statistics."""
        try:
            return await self.repository.get_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting expense stats for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to retrieve expense statistics",
                context={"user_id": user_id}
            )

    async def get_overdue_invoices(self, user_id: str) -> OverdueExpensesListResponse:
        """Get overdue invoices."""
        try:
            return await self.repository.get_overdue_expenses(user_id)
        except Exception as e:
            logger.error(f"Error getting overdue expenses for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to retrieve overdue expenses",
                context={"user_id": user_id}
            )

    # Override BaseService validation hooks
    async def _pre_create_validation(self, entity_data: Dict[str, Any], user_id: str) -> None:
        """Expense-specific pre-create validation."""
        await self._validate_expense_data(entity_data, user_id)
        
        # Check for duplicate invoice numbers
        if entity_data.get('invoice_number'):
            await self._check_duplicate_invoice_number(
                user_id, 
                entity_data['invoice_number']
            )

    async def _pre_update_validation(
        self, 
        entity: Expense, 
        update_data: Dict[str, Any], 
        user_id: str
    ) -> None:
        """Expense-specific pre-update validation."""
        # Prevent modification of paid invoices
        if entity.payment_status == PaymentStatus.PAID and entity.expense_type == ExpenseType.INVOICE:
            restricted_fields = ['base_amount', 'tax_amount', 'total_amount', 'category_id']
            if any(field in update_data for field in restricted_fields):
                raise PaidInvoiceModificationError(  # ✅ CORRECT exception
                    detail="Cannot modify paid invoice amounts or category",
                    context={"expense_id": str(entity.id)}
                )
        
        if update_data:
            await self._validate_expense_data(update_data, user_id, is_update=True)

    async def _pre_delete_validation(self, entity: Expense, user_id: str) -> None:
        """Expense-specific pre-delete validation."""
        if entity.payment_status == PaymentStatus.PAID and entity.expense_type == ExpenseType.INVOICE:
            raise PaidInvoiceModificationError(  # ✅ CORRECT exception
                detail="Cannot delete paid invoices",
                context={"expense_id": str(entity.id)}
            )

    # Private validation methods
    async def _validate_expense_data(
        self, 
        data: Dict[str, Any], 
        user_id: str, 
        is_update: bool = False
    ) -> None:
        """Validate expense data."""
        if not is_update:
            self._validate_required_fields(data, ['description', 'expense_date'])
        
        # Validate amounts
        for amount_field in ['base_amount', 'tax_amount', 'total_amount']:
            if amount_field in data and data[amount_field] is not None:
                self._validate_amount(data[amount_field], amount_field)
        
        # Validate currency
        if 'currency' in data and data['currency'] not in SUPPORTED_CURRENCIES:
            raise InvalidCurrencyError(  # ✅ CORRECT exception
                detail=f"Unsupported currency. Must be one of: {', '.join(SUPPORTED_CURRENCIES)}",
                context={"currency": data['currency']}
            )

    def _validate_amount(self, amount: Decimal, field_name: str) -> None:
        """Validate amount is within acceptable range."""
        if amount < MIN_EXPENSE_AMOUNT or amount > MAX_EXPENSE_AMOUNT:
            raise InvalidAmountError(  # ✅ CORRECT exception
                detail=f"Amount must be between {MIN_EXPENSE_AMOUNT} and {MAX_EXPENSE_AMOUNT}",
                context={"field": field_name, "amount": str(amount)}
            )

    async def _check_duplicate_invoice_number(
        self, 
        user_id: str, 
        invoice_number: str, 
        exclude_id: uuid.UUID = None
    ) -> None:
        """Check for duplicate invoice numbers."""
        is_duplicate = await self.repository.check_duplicate_invoice_number(
            user_id, invoice_number, exclude_id
        )
        if is_duplicate:
            raise DuplicateInvoiceNumberError(  # ✅ CORRECT exception
                detail=f"Invoice number '{invoice_number}' already exists",
                context={"invoice_number": invoice_number}
            )

    def _calculate_tax_amount(self, base_amount: Decimal, tax_rate: Decimal) -> Decimal:
        """Calculate tax amount from base amount and rate."""
        return (base_amount * tax_rate / Decimal('100')).quantize(Decimal('0.01'))
