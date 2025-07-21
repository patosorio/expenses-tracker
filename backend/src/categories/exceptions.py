# Category-specific exceptions

from core.exceptions import BaseNotFoundError, BaseValidationError, BaseBadRequestError

class CategoryNotFoundError(BaseNotFoundError):
    """Raised when a category is not found in the database"""
    pass

class CategoryValidationError(BaseValidationError):
    """Raised when category data validation fails"""
    pass

class CategoryAlreadyExistsError(BaseBadRequestError):
    """Raised when trying to create a category with a name that already exists at the same level"""
    pass

class InvalidCategoryParentError(BaseBadRequestError):
    """Raised when trying to set an invalid parent for a category"""
    pass

class CategoryTypeConflictError(BaseBadRequestError):
    """Raised when parent and child categories have different types"""
    pass

class CircularCategoryReferenceError(BaseBadRequestError):
    """Raised when trying to create a circular parent-child relationship"""
    pass

class CategoryDeleteError(BaseBadRequestError):
    """Raised when category deletion fails"""
    pass

class CategoryUpdateError(BaseBadRequestError):
    """Raised when category update fails"""
    pass

class InvalidCategoryHierarchyError(BaseBadRequestError):
    """Raised when category hierarchy is invalid"""
    pass 