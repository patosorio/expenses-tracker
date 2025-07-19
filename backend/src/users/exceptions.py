# Users module exceptions

class UserNotFoundError(Exception):
    """Raised when a user is not found in the database"""
    pass

class DuplicateEmailError(Exception):
    """Raised when trying to create/update a user with an email that already exists"""
    pass

class UserValidationError(Exception):
    """Raised when user data validation fails"""
    pass

class UserUpdateError(Exception):
    """Raised when user update fails"""
    pass

class UserDeleteError(Exception):
    """Raised when user deletion fails"""
    pass

class UserSettingsNotFoundError(Exception):
    """Raised when user settings are not found"""
    pass

class UserSettingsUpdateError(Exception):
    """Raised when user settings update fails"""
    pass

class InvalidUserRoleError(Exception):
    """Raised when an invalid user role is provided"""
    pass

class InvalidUserStatusError(Exception):
    """Raised when an invalid user status is provided"""
    pass

class UserAuthenticationError(Exception):
    """Raised when user authentication fails"""
    pass 