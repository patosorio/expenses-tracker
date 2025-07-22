# Contact-specific exceptions
from ..core.shared.exceptions import (
    NotFoundError,
    ValidationError,
    BadRequestError,
    ConflictError)

class ContactNotFoundError(NotFoundError):
    """Contact not found in database."""
    detail: str = "Contact not found"
    error_code: str = "CONTACT_NOT_FOUND"


class ContactValidationError(ValidationError):
    """Contact data validation failed."""
    detail: str = "Invalid contact data"
    error_code: str = "CONTACT_VALIDATION_FAILED"


class ContactAlreadyExistsError(ConflictError):
    """Contact with same name already exists for this user."""
    detail: str = "Contact with this name already exists"
    error_code: str = "CONTACT_ALREADY_EXISTS"


class DuplicateContactEmailError(ConflictError):
    """Contact with same email already exists for this user."""
    detail: str = "Contact with this email already exists"
    error_code: str = "DUPLICATE_CONTACT_EMAIL"


class InvalidContactTypeError(ValidationError):
    """Invalid contact type specified."""
    detail: str = "Invalid contact type"
    error_code: str = "INVALID_CONTACT_TYPE"


class ContactUpdateError(BadRequestError):
    """Contact update operation failed."""
    detail: str = "Failed to update contact"
    error_code: str = "CONTACT_UPDATE_FAILED"


class ContactDeleteError(BadRequestError):
    """Contact deletion operation failed."""
    detail: str = "Failed to delete contact"
    error_code: str = "CONTACT_DELETE_FAILED"


class InvalidContactSearchError(ValidationError):
    """Invalid contact search parameters provided."""
    detail: str = "Invalid search parameters"
    error_code: str = "INVALID_CONTACT_SEARCH"


class ContactInUseError(BadRequestError):
    """Cannot delete contact that is being used in expenses or invoices."""
    detail: str = "Contact is currently in use"
    error_code: str = "CONTACT_IN_USE"


class InvalidContactEmailError(ValidationError):
    """Invalid email format provided for contact."""
    detail: str = "Invalid email format"
    error_code: str = "INVALID_CONTACT_EMAIL"


class InvalidContactPhoneError(ValidationError):
    """Invalid phone number format provided for contact."""
    detail: str = "Invalid phone number format"
    error_code: str = "INVALID_CONTACT_PHONE"


class ContactTaxNumberError(ValidationError):
    """Invalid tax number format for contact."""
    detail: str = "Invalid tax number format"
    error_code: str = "INVALID_TAX_NUMBER"