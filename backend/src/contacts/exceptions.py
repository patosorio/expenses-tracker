# Contact-specific exceptions
from core.exceptions import BaseNotFoundError, BaseValidationError, BaseBadRequestError

class ContactNotFoundError(BaseNotFoundError):
    """Raised when a contact is not found in the database"""
    pass

class ContactValidationError(BaseValidationError):
    """Raised when contact data validation fails"""
    pass

class ContactAlreadyExistsError(BaseBadRequestError):
    """Raised when trying to create a contact that already exists"""
    pass

class InvalidContactTypeError(BaseBadRequestError):
    """Raised when contact type is invalid for the operation"""
    pass

class ContactUpdateError(BaseBadRequestError):
    """Raised when contact update fails"""
    pass

class ContactDeleteError(BaseBadRequestError):
    """Raised when contact deletion fails"""
    pass

class DuplicateContactEmailError(BaseBadRequestError):
    """Raised when trying to create a contact with an email that already exists"""
    pass

class InvalidContactSearchError(BaseBadRequestError):
    """Raised when contact search parameters are invalid"""
    pass 