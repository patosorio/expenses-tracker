# Core exceptions - Global exceptions used across multiple modules
from typing import Any, Dict, Optional


class AppBaseException(Exception):
    """Base class for all application exception
    with structured error handling."""
    
    status_code: int = 500
    detail: str = "An unexpected error occurred"
    error_code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def __init__(
        self, 
        detail: Optional[str] = None, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        if detail:
            self.detail = detail
        if error_code:
            self.error_code = error_code
        if context:
            self.context = context
        super().__init__(self.detail)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = {
            "error": True,
            "status_code": self.status_code,
            "detail": self.detail,
        }
        if self.error_code:
            result["error_code"] = self.error_code
        if self.context:
            result["context"] = self.context
        return result


class BadRequestError(AppBaseException):
    """400 - Bad request exception."""
    status_code: int = 400
    detail: str = "Invalid request"


class UnauthorizedError(AppBaseException):
    """401 - Unauthorized access exception."""
    status_code: int = 401
    detail: str = "Authentication required"


class ForbiddenError(AppBaseException):
    """403 - Forbidden access exception."""  
    status_code: int = 403
    detail: str = "Access forbidden"


class NotFoundError(AppBaseException):
    """404 - Resource not found exception."""
    status_code: int = 404
    detail: str = "Resource not found"


class ConflictError(AppBaseException):
    """409 - Resource conflict exception."""
    status_code: int = 409
    detail: str = "Resource conflict"


class ValidationError(AppBaseException):
    """422 - Validation error exception."""
    status_code: int = 422
    detail: str = "Validation failed"


class TooManyRequestsError(AppBaseException):
    """429 - Rate limit exceeded exception."""
    status_code: int = 429
    detail: str = "Too many requests"


class InternalServerError(AppBaseException):
    """500 - Internal server error exception."""
    status_code: int = 500
    detail: str = "Internal server error"


class ServiceUnavailableError(AppBaseException):
    """503 - Service unavailable exception."""
    status_code: int = 503
    detail: str = "Service temporarily unavailable"


class ExternalServiceError(AppBaseException):
    """502 - External service error (OCR, AI services, etc.)."""
    status_code: int = 502  
    detail: str = "External service error"