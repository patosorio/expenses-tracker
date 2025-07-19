# Category-specific exceptions

class CategoryNotFoundError(Exception):
    """Raised when a category is not found in the database"""
    pass

class CategoryValidationError(Exception):
    """Raised when category data validation fails"""
    pass

class CategoryAlreadyExistsError(Exception):
    """Raised when trying to create a category with a name that already exists at the same level"""
    pass

class InvalidCategoryParentError(Exception):
    """Raised when trying to set an invalid parent for a category"""
    pass

class CategoryTypeConflictError(Exception):
    """Raised when parent and child categories have different types"""
    pass

class CircularCategoryReferenceError(Exception):
    """Raised when trying to create a circular parent-child relationship"""
    pass

class CategoryDeleteError(Exception):
    """Raised when category deletion fails"""
    pass

class CategoryUpdateError(Exception):
    """Raised when category update fails"""
    pass

class InvalidCategoryHierarchyError(Exception):
    """Raised when category hierarchy is invalid"""
    pass 