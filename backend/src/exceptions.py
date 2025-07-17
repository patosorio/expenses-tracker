# Global exceptions

class NotFoundError(Exception):
    """Generic not found error"""
    pass

class ValidationError(Exception):
    """Generic validation error"""
    pass

class UserNotFoundError(NotFoundError):
    """Raised when a user is not found in the database"""
    pass

class DuplicateEmailError(Exception):
    """Raised when trying to create/update a user with an email that already exists"""
    pass

class CategoryNotFoundError(NotFoundError):
    """Raised when a category is not found in the database"""
    pass

class DuplicateCategoryError(ValidationError):
    """Raised when trying to create a category with a name that already exists at the same level"""
    pass

class InvalidCategoryParentError(ValidationError):
    """Raised when trying to set an invalid parent for a category"""
    pass

class CategoryTypeConflictError(ValidationError):
    """Raised when parent and child categories have different types"""
    pass

class CircularCategoryReferenceError(ValidationError):
    """Raised when trying to create a circular parent-child relationship"""
    pass

class BusinessSettingsNotFoundError(NotFoundError):
    """Raised when business settings are not found"""
    pass

class TaxConfigurationNotFoundError(NotFoundError):
    """Raised when a tax configuration is not found"""
    pass

class TeamMemberNotFoundError(NotFoundError):
    """Raised when a team member is not found"""
    pass

class TeamInvitationNotFoundError(NotFoundError):
    """Raised when a team invitation is not found"""
    pass

class TeamInvitationExpiredError(ValidationError):
    """Raised when a team invitation has expired"""
    pass

class DuplicateTeamMemberError(ValidationError):
    """Raised when trying to invite a user who is already a team member"""
    pass

class ContactNotFoundError(NotFoundError):
    """Raised when a contact is not found"""
    pass

class ContactAlreadyExistsError(ValidationError):
    """Raised when trying to create a contact that already exists"""
    pass