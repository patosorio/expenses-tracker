# Global exceptions - Only truly global exceptions that are used across multiple modules

class NotFoundError(Exception):
    """Generic not found error - base class for all not found errors"""
    pass

class ValidationError(Exception):
    """Generic validation error - base class for all validation errors"""
    pass