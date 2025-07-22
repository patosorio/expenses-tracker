# Team module exceptions
from ..core.shared.exceptions import (
    NotFoundError,
    ValidationError,
    BadRequestError,
    ConflictError,
    UnauthorizedError,
    ExternalServiceError
)


class TeamMemberNotFoundError(NotFoundError):
    """Team member not found in organization."""
    detail: str = "Team member not found"
    error_code: str = "TEAM_MEMBER_NOT_FOUND"


class TeamMemberValidationError(ValidationError):
    """Team member data validation failed."""
    detail: str = "Invalid team member data"
    error_code: str = "TEAM_MEMBER_VALIDATION_FAILED"


class TeamMemberAlreadyExistsError(ConflictError):
    """Team member with this email already exists."""
    detail: str = "Team member already exists"
    error_code: str = "TEAM_MEMBER_ALREADY_EXISTS"


class DuplicateTeamMemberError(ConflictError):
    """User is already a team member or invited."""
    detail: str = "User is already a team member"
    error_code: str = "DUPLICATE_TEAM_MEMBER"


class TeamInvitationNotFoundError(NotFoundError):
    """Team invitation not found or invalid."""
    detail: str = "Team invitation not found"
    error_code: str = "TEAM_INVITATION_NOT_FOUND"


class TeamInvitationValidationError(ValidationError):
    """Team invitation data validation failed."""
    detail: str = "Invalid invitation data"
    error_code: str = "TEAM_INVITATION_VALIDATION_FAILED"


class TeamInvitationExpiredError(BadRequestError):
    """Team invitation has expired or is no longer valid."""
    detail: str = "Team invitation has expired"
    error_code: str = "TEAM_INVITATION_EXPIRED"


class TeamInvitationError(BadRequestError):
    """Failed to create or process team invitation."""
    detail: str = "Team invitation failed"
    error_code: str = "TEAM_INVITATION_FAILED"


class TeamValidationError(ValidationError):
    """Team data validation failed."""
    detail: str = "Invalid team data"
    error_code: str = "TEAM_VALIDATION_FAILED"


class TeamMemberUpdateError(BadRequestError):
    """Failed to update team member."""
    detail: str = "Failed to update team member"
    error_code: str = "TEAM_MEMBER_UPDATE_FAILED"


class TeamMemberDeleteError(BadRequestError):
    """Failed to remove team member."""
    detail: str = "Failed to remove team member"
    error_code: str = "TEAM_MEMBER_DELETE_FAILED"


class InvalidTeamRoleError(ValidationError):
    """Invalid team role specified."""
    detail: str = "Invalid team role"
    error_code: str = "INVALID_TEAM_ROLE"


class InvalidTeamPermissionsError(ValidationError):
    """Invalid team permissions specified."""
    detail: str = "Invalid team permissions"
    error_code: str = "INVALID_TEAM_PERMISSIONS"


class TeamSizeLimitExceededError(BadRequestError):
    """Organization has reached maximum team size."""
    detail: str = "Team size limit exceeded"
    error_code: str = "TEAM_SIZE_LIMIT_EXCEEDED"


class InsufficientTeamPermissionsError(UnauthorizedError):
    """User lacks permissions for this team operation."""
    detail: str = "Insufficient team permissions"
    error_code: str = "INSUFFICIENT_TEAM_PERMISSIONS"


class TeamMemberSelfRemovalError(BadRequestError):
    """Team owner cannot remove themselves."""
    detail: str = "Cannot remove yourself from team"
    error_code: str = "TEAM_MEMBER_SELF_REMOVAL"


class InvalidInvitationTokenError(ValidationError):
    """Invalid or malformed invitation token."""
    detail: str = "Invalid invitation token"
    error_code: str = "INVALID_INVITATION_TOKEN"


class TeamEmailDeliveryError(ExternalServiceError):
    """Failed to send team invitation email."""
    detail: str = "Failed to send invitation email"
    error_code: str = "TEAM_EMAIL_DELIVERY_FAILED"


class TeamRoleHierarchyError(BadRequestError):
    """Invalid role hierarchy operation."""
    detail: str = "Invalid role hierarchy"
    error_code: str = "TEAM_ROLE_HIERARCHY_ERROR"


class TeamDepartmentNotFoundError(NotFoundError):
    """Team department not found."""
    detail: str = "Department not found"
    error_code: str = "TEAM_DEPARTMENT_NOT_FOUND"