# Expense-specific exceptions
from ..core.shared.exceptions import (
    NotFoundError,
    ValidationError,
    BadRequestError,
    ConflictError,
    ExternalServiceError
)


class ExpenseNotFoundError(NotFoundError):
    """Expense record not found in database."""
    detail: str = "Expense not found"
    error_code: str = "EXPENSE_NOT_FOUND"


class ExpenseValidationError(ValidationError):
    """Expense data validation failed."""
    detail: str = "Invalid expense data"
    error_code: str = "EXPENSE_VALIDATION_FAILED"


class ExpenseAlreadyExistsError(ConflictError):
    """Expense with similar details already exists."""
    detail: str = "Similar expense already exists"
    error_code: str = "EXPENSE_ALREADY_EXISTS"


class InvalidExpenseTypeError(ValidationError):
    """Invalid expense type for the requested operation."""
    detail: str = "Invalid expense type for this operation"
    error_code: str = "INVALID_EXPENSE_TYPE"


class InvalidPaymentStatusError(BadRequestError):
    """Invalid payment status transition."""
    detail: str = "Invalid payment status transition"
    error_code: str = "INVALID_PAYMENT_STATUS"


class ExpenseUpdateError(BadRequestError):
    """Failed to update expense record."""
    detail: str = "Failed to update expense"
    error_code: str = "EXPENSE_UPDATE_FAILED"


class ExpenseDeleteError(BadRequestError):
    """Failed to delete expense record."""
    detail: str = "Failed to delete expense"
    error_code: str = "EXPENSE_DELETE_FAILED"


class PaidInvoiceModificationError(BadRequestError):
    """Cannot modify a paid invoice."""
    detail: str = "Cannot modify paid invoice"
    error_code: str = "PAID_INVOICE_MODIFICATION"


# Document & OCR Related Exceptions
class DocumentAnalysisNotFoundError(NotFoundError):
    """OCR document analysis not found."""
    detail: str = "Document analysis not found"
    error_code: str = "DOCUMENT_ANALYSIS_NOT_FOUND"


class AttachmentNotFoundError(NotFoundError):
    """Expense attachment not found."""
    detail: str = "Expense attachment not found"
    error_code: str = "ATTACHMENT_NOT_FOUND"


class OCRProcessingError(ExternalServiceError):
    """Google Vision OCR processing failed."""
    detail: str = "OCR processing failed"
    error_code: str = "OCR_PROCESSING_FAILED"


class InvalidFileTypeError(ValidationError):
    """Unsupported file type for processing."""
    detail: str = "Unsupported file type"
    error_code: str = "INVALID_FILE_TYPE"


class FileSizeLimitExceededError(ValidationError):
    """Uploaded file exceeds size limit."""
    detail: str = "File size exceeds limit"
    error_code: str = "FILE_SIZE_LIMIT_EXCEEDED"


class DocumentAnalysisFailedError(ExternalServiceError):
    """Document analysis processing failed."""
    detail: str = "Document analysis failed"
    error_code: str = "DOCUMENT_ANALYSIS_FAILED"


# Tax & Financial Calculation Exceptions
class InvalidTaxCalculationError(ValidationError):
    """Tax calculation failed due to invalid data."""
    detail: str = "Invalid tax calculation"
    error_code: str = "INVALID_TAX_CALCULATION"


class TaxConfigurationNotFoundError(NotFoundError):
    """Tax configuration not found."""
    detail: str = "Tax configuration not found"
    error_code: str = "TAX_CONFIG_NOT_FOUND"


class InvalidAmountError(ValidationError):
    """Invalid monetary amount provided."""
    detail: str = "Invalid amount value"
    error_code: str = "INVALID_AMOUNT"


class CategoryNotFoundError(NotFoundError):
    """Expense category not found."""
    detail: str = "Expense category not found"
    error_code: str = "CATEGORY_NOT_FOUND"


class InvalidCategoryTypeError(ValidationError):
    """Category type is not valid for expenses."""
    detail: str = "Category must be an expense category"
    error_code: str = "INVALID_CATEGORY_TYPE"


# Business Logic Exceptions
class InvoiceRequiredFieldsError(ValidationError):
    """Required fields missing for invoice creation."""
    detail: str = "Required invoice fields missing"
    error_code: str = "INVOICE_REQUIRED_FIELDS"


class DuplicateInvoiceNumberError(ConflictError):
    """Invoice number already exists."""
    detail: str = "Invoice number already exists"
    error_code: str = "DUPLICATE_INVOICE_NUMBER"


class ExpenseOverdueError(BadRequestError):
    """Expense is overdue."""
    detail: str = "Expense payment is overdue"
    error_code: str = "EXPENSE_OVERDUE"


class ContactNotFoundError(NotFoundError):
    """Contact associated with expense not found."""
    detail: str = "Contact not found"
    error_code: str = "CONTACT_NOT_FOUND"


class InvalidCurrencyError(ValidationError):
    """Invalid currency code provided."""
    detail: str = "Invalid currency code"
    error_code: str = "INVALID_CURRENCY"


class ExpenseImportError(BadRequestError):
    """Failed to import expense from external source."""
    detail: str = "Failed to import expense"
    error_code: str = "EXPENSE_IMPORT_FAILED"


class RecurringExpenseError(BadRequestError):
    """Error with recurring expense configuration."""
    detail: str = "Recurring expense configuration error"
    error_code: str = "RECURRING_EXPENSE_ERROR"