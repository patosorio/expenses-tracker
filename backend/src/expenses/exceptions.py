# Expense-specific exceptions
from core.exceptions import BaseNotFoundError, BaseValidationError, BaseBadRequestError

class ExpenseNotFoundError(BaseNotFoundError):
    """Raised when an expense is not found in the database"""
    pass

class ExpenseValidationError(BaseValidationError):
    """Raised when expense data validation fails"""
    pass

class ExpenseAlreadyExistsError(BaseBadRequestError):
    """Raised when trying to create an expense that already exists"""
    pass

class InvalidExpenseTypeError(BaseBadRequestError):
    """Raised when expense type is invalid for the operation"""
    pass

class InvalidPaymentStatusError(BaseBadRequestError):
    """Raised when payment status transition is invalid"""
    pass

class DocumentAnalysisNotFoundError(BaseNotFoundError):
    """Raised when document analysis is not found"""
    pass

class AttachmentNotFoundError(BaseNotFoundError):
    """Raised when expense attachment is not found"""
    pass

class InvalidTaxCalculationError(BaseBadRequestError):
    """Raised when tax calculation fails"""
    pass

class ExpenseUpdateError(BaseBadRequestError):
    """Raised when expense update operation fails"""
    pass

class ExpenseDeleteError(BaseBadRequestError):
    """Raised when expense deletion fails"""
    pass 