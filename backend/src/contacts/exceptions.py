# Contact-specific exceptions

class ContactNotFoundError(Exception):
    """Raised when a contact is not found in the database"""
    pass

class ContactValidationError(Exception):
    """Raised when contact data validation fails"""
    pass

class ContactAlreadyExistsError(Exception):
    """Raised when trying to create a contact that already exists"""
    pass

class InvalidContactTypeError(Exception):
    """Raised when contact type is invalid for the operation"""
    pass

class ContactUpdateError(Exception):
    """Raised when contact update fails"""
    pass

class ContactDeleteError(Exception):
    """Raised when contact deletion fails"""
    pass

class DuplicateContactEmailError(Exception):
    """Raised when trying to create a contact with an email that already exists"""
    pass

class InvalidContactSearchError(Exception):
    """Raised when contact search parameters are invalid"""
    pass 