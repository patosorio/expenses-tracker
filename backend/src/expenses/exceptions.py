# Expense-specific exceptions

class ExpenseNotFoundError(Exception):
    """Raised when an expense is not found in the database"""
    pass

class ExpenseValidationError(Exception):
    """Raised when expense data validation fails"""
    pass

class ExpenseAlreadyExistsError(Exception):
    """Raised when trying to create an expense that already exists"""
    pass

class InvalidExpenseTypeError(Exception):
    """Raised when expense type is invalid for the operation"""
    pass

class InvalidPaymentStatusError(Exception):
    """Raised when payment status transition is invalid"""
    pass

class DocumentAnalysisNotFoundError(Exception):
    """Raised when document analysis is not found"""
    pass

class AttachmentNotFoundError(Exception):
    """Raised when expense attachment is not found"""
    pass

class InvalidTaxCalculationError(Exception):
    """Raised when tax calculation fails"""
    pass

class ExpenseUpdateError(Exception):
    """Raised when expense update operation fails"""
    pass

class ExpenseDeleteError(Exception):
    """Raised when expense deletion fails"""
    pass 