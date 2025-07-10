# Global exceptions

class UserNotFoundError(Exception):
    """Raised when a user is not found in the database"""
    pass

class DuplicateEmailError(Exception):
    """Raised when trying to create/update a user with an email that already exists"""
    pass