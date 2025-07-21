# Team module exceptions
from core.exceptions import BaseNotFoundError, BaseValidationError, BaseBadRequestError

class TeamMemberNotFoundError(BaseNotFoundError):
    """Raised when a team member is not found"""
    pass

class TeamMemberValidationError(BaseValidationError):
    """Raised when team member validation fails"""
    pass

class TeamMemberAlreadyExistsError(BaseBadRequestError):
    """Raised when a team member already exists"""
    pass

class TeamInvitationNotFoundError(BaseNotFoundError):
    """Raised when a team invitation is not found"""
    pass

class TeamInvitationValidationError(BaseValidationError):
    """Raised when team invitation validation fails"""
    pass

class TeamInvitationExpiredError(BaseBadRequestError):
    """Raised when a team invitation has expired"""
    pass

class DuplicateTeamMemberError(BaseBadRequestError):
    """Raised when trying to invite a user who is already a team member"""
    pass

class TeamValidationError(BaseValidationError):
    """Raised when team data validation fails"""
    pass

class TeamMemberUpdateError(BaseBadRequestError):
    """Raised when team member update fails"""
    pass

class TeamMemberDeleteError(BaseBadRequestError):
    """Raised when team member deletion fails"""
    pass

class InvalidTeamRoleError(BaseBadRequestError):
    """Raised when an invalid team role is provided"""
    pass

class InvalidTeamPermissionsError(BaseBadRequestError):
    """Raised when invalid team permissions are provided"""
    pass

class TeamInvitationError(BaseBadRequestError):
    """Raised when team invitation creation fails"""
    pass 