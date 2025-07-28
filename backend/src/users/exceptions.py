# Users module exceptions
from ..core.shared.exceptions import (
    NotFoundError, 
    ValidationError, 
    ConflictError, 
    UnauthorizedError
)


class UserNotFoundError(NotFoundError):
    """User not found in the system."""
    detail: str = "User not found"
    error_code: str = "USER_NOT_FOUND"


class UserAlreadyExistsError(ConflictError):
    """User with email already exists."""
    detail: str = "User with this email already exists"
    error_code: str = "USER_ALREADY_EXISTS"


class InvalidUserDataError(ValidationError):
    """Invalid user profile data provided."""
    detail: str = "Invalid user data provided"
    error_code: str = "INVALID_USER_DATA"


class InvalidEmailError(ValidationError):
    """Invalid email format or structure provided."""
    detail: str = "Invalid email format"
    error_code: str = "INVALID_EMAIL_ERROR"


class InvalidPasswordError(ValidationError):
    """Password doesn't meet security requirements."""
    detail: str = "Password doesn't meet security requirements"
    error_code: str = "INVALID_PASSWORD"


class InvalidCredentialsError(UnauthorizedError):
    """Invalid login credentials provided."""
    detail: str = "Invalid email or password"
    error_code: str = "INVALID_CREDENTIALS"


class AccountDeactivatedError(UnauthorizedError):
    """User account is deactivated."""
    detail: str = "Account is deactivated"
    error_code: str = "ACCOUNT_DEACTIVATED"


class EmailVerificationRequiredError(UnauthorizedError):
    """Email verification required to proceed."""
    detail: str = "Email verification required"
    error_code: str = "EMAIL_VERIFICATION_REQUIRED"


class PasswordResetTokenInvalidError(ValidationError):
    """Password reset token is invalid or expired."""
    detail: str = "Invalid or expired password reset token"
    error_code: str = "INVALID_RESET_TOKEN"


class DuplicateEmailError(ConflictError):
    """Legacy alias for UserAlreadyExistsError."""
    detail: str = "User with this email already exists"
    error_code: str = "USER_ALREADY_EXISTS"


class UserValidationError(ValidationError):
    """Legacy alias for InvalidUserDataError."""
    detail: str = "Invalid user data provided"
    error_code: str = "INVALID_USER_DATA"


class UserUpdateError(ValidationError):
    """User update operation failed."""
    detail: str = "Failed to update user"
    error_code: str = "USER_UPDATE_FAILED"


class UserSettingsNotFoundError(NotFoundError):
    """User settings not found."""
    detail: str = "User settings not found"
    error_code: str = "USER_SETTINGS_NOT_FOUND"