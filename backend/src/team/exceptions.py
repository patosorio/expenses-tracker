# Team module exceptions

class TeamMemberNotFoundError(Exception):
    """Raised when a team member is not found"""
    pass

class TeamMemberValidationError(Exception):
    """Raised when team member validation fails"""
    pass

class TeamMemberAlreadyExistsError(Exception):
    """Raised when a team member already exists"""
    pass

class TeamInvitationNotFoundError(Exception):
    """Raised when a team invitation is not found"""
    pass

class TeamInvitationValidationError(Exception):
    """Raised when team invitation validation fails"""
    pass

class TeamInvitationExpiredError(Exception):
    """Raised when a team invitation has expired"""
    pass

class DuplicateTeamMemberError(Exception):
    """Raised when trying to invite a user who is already a team member"""
    pass

class TeamValidationError(Exception):
    """Raised when team data validation fails"""
    pass

class TeamMemberUpdateError(Exception):
    """Raised when team member update fails"""
    pass

class TeamMemberDeleteError(Exception):
    """Raised when team member deletion fails"""
    pass

class InvalidTeamRoleError(Exception):
    """Raised when an invalid team role is provided"""
    pass

class InvalidTeamPermissionsError(Exception):
    """Raised when invalid team permissions are provided"""
    pass

class TeamInvitationError(Exception):
    """Raised when team invitation creation fails"""
    pass 