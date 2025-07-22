# Category-specific exceptions

from ..core.shared.exceptions import (
    NotFoundError,
    ValidationError,
    BadRequestError,
    ConflictError
)

class CategoryNotFoundError(NotFoundError):
    """Category not found in database."""
    detail: str = "Category not found"
    error_code: str = "CATEGORY_NOT_FOUND"


class CategoryValidationError(ValidationError):
    """Category data validation failed."""
    detail: str = "Invalid category data"
    error_code: str = "CATEGORY_VALIDATION_FAILED"


class CategoryAlreadyExistsError(ConflictError):
    """Category with same name already exists at this level."""
    detail: str = "Category name already exists at this level"
    error_code: str = "CATEGORY_ALREADY_EXISTS"


class InvalidCategoryParentError(BadRequestError):
    """Invalid parent category specified."""
    detail: str = "Invalid parent category"
    error_code: str = "INVALID_CATEGORY_PARENT"


class CategoryTypeConflictError(BadRequestError):
    """Parent and child categories have conflicting types."""
    detail: str = "Category type conflicts with parent type"
    error_code: str = "CATEGORY_TYPE_CONFLICT"


class CircularCategoryReferenceError(BadRequestError):
    """Circular parent-child relationship detected."""
    detail: str = "Circular category reference not allowed"
    error_code: str = "CIRCULAR_CATEGORY_REFERENCE"


class CategoryDeleteError(BadRequestError):
    """Category deletion failed due to business rules."""
    detail: str = "Cannot delete category"
    error_code: str = "CATEGORY_DELETE_FAILED"


class CategoryUpdateError(BadRequestError):
    """Category update operation failed."""
    detail: str = "Failed to update category"
    error_code: str = "CATEGORY_UPDATE_FAILED"


class InvalidCategoryHierarchyError(BadRequestError):
    """Category hierarchy structure is invalid."""
    detail: str = "Invalid category hierarchy"
    error_code: str = "INVALID_CATEGORY_HIERARCHY"


# Additional business-specific category exceptions

class CategoryDepthLimitExceededError(ValidationError):
    """Category hierarchy depth limit exceeded."""
    detail: str = "Category hierarchy depth limit exceeded"
    error_code: str = "CATEGORY_DEPTH_LIMIT_EXCEEDED"


class CategoryHasChildrenError(BadRequestError):
    """Cannot perform operation on category with children."""
    detail: str = "Category has child categories"
    error_code: str = "CATEGORY_HAS_CHILDREN"


class CategoryInUseError(BadRequestError):
    """Cannot delete/modify category that is in use."""
    detail: str = "Category is currently in use"
    error_code: str = "CATEGORY_IN_USE"


class DefaultCategoryModificationError(BadRequestError):
    """Cannot modify or delete default system categories."""
    detail: str = "Cannot modify default system category"
    error_code: str = "DEFAULT_CATEGORY_MODIFICATION"


class CategoryNameTooLongError(ValidationError):
    """Category name exceeds maximum length."""
    detail: str = "Category name is too long"
    error_code: str = "CATEGORY_NAME_TOO_LONG"


class InvalidCategoryColorError(ValidationError):
    """Invalid color format for category."""
    detail: str = "Invalid category color format"
    error_code: str = "INVALID_CATEGORY_COLOR"


class CategoryPermissionError(BadRequestError):
    """Insufficient permissions for category operation."""
    detail: str = "Insufficient permissions for this category operation"
    error_code: str = "CATEGORY_PERMISSION_DENIED"


class CategoryArchiveError(BadRequestError):
    """Cannot archive category due to business rules."""
    detail: str = "Cannot archive category"
    error_code: str = "CATEGORY_ARCHIVE_FAILED"
