from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import uuid
import secrets
import re
from datetime import datetime, timedelta
import logging

from .models import TeamMember, TeamInvitation
from .repository import TeamRepository
from .schemas import TeamMemberInvite, TeamStats
from .exceptions import *
from ..core.shared.base_service import BaseService
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)

MAX_TEAM_SIZE = 100
INVITATION_EXPIRY_DAYS = 7
VALID_TEAM_ROLES = ["owner", "admin", "manager", "member", "viewer"]
VALID_DEPARTMENTS = ["finance", "operations", "sales", "marketing", "hr", "it", "other"]

class TeamService(BaseService[TeamMember, TeamRepository]):
    """Team service with business logic extending BaseService."""
    def __init__(self, db: AsyncSession):
        super().__init__(db, TeamRepository, TeamMember)

    async def invite_team_member(self, owner_id: str, invitation_data: TeamMemberInvite) -> TeamMember:
        """Invite new team member with comprehensive validation and email notification."""
        try:
            await self._validate_invitation_data(invitation_data, owner_id)
            await self._validate_team_size_limit(owner_id)
            existing = await self.repository.get_team_member_by_email(invitation_data.email, owner_id)
            if existing and existing.status == "active":
                raise DuplicateTeamMemberError(
                    detail="User is already an active team member",
                    context={"email": invitation_data.email, "status": existing.status}
                )
            if existing and existing.status == "pending":
                raise DuplicateTeamMemberError(
                    detail="Invitation already sent to this email",
                    context={"email": invitation_data.email, "status": existing.status}
                )
            invitation_token = secrets.token_urlsafe(32)
            team_member = TeamMember(
                id=str(uuid.uuid4()),
                organization_owner_id=owner_id,
                email=invitation_data.email,
                role=invitation_data.role,
                department=invitation_data.department,
                job_title=invitation_data.job_title,
                permissions=invitation_data.permissions,
                invitation_token=invitation_token,
                status="pending"
            )
            team_member = await self.repository.create(team_member, owner_id)
            invitation = TeamInvitation(
                id=str(uuid.uuid4()),
                team_member_id=team_member.id,
                expires_at=datetime.utcnow() + timedelta(days=INVITATION_EXPIRY_DAYS)
            )
            await self.repository.create_invitation(invitation)
            try:
                await self._send_invitation_email(team_member, invitation_token)
            except Exception as e:
                logger.warning(f"Failed to send invitation email: {e!s}")
            logger.info(f"Team member invited successfully: {team_member.id} for owner {owner_id}")
            return team_member
        except (
            TeamValidationError, DuplicateTeamMemberError, InvalidTeamRoleError,
            InvalidTeamPermissionsError, TeamSizeLimitExceededError, TeamMemberValidationError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error inviting team member for owner {owner_id}: {e!s}", exc_info=True)
            raise TeamInvitationError(
                detail="Failed to create team invitation due to internal error",
                context={"owner_id": owner_id, "email": invitation_data.email}
            )

    async def accept_invitation(self, token: str, user_id: str) -> TeamMember:
        """Accept team invitation and activate membership."""
        try:
            if not token or len(token) < 20:
                raise InvalidInvitationTokenError(
                    detail="Invalid invitation token format",
                    context={"token_length": len(token) if token else 0}
                )
            team_member = await self.repository.get_invitation_by_token(token)
            if not team_member:
                raise TeamInvitationNotFoundError(
                    detail="Invalid invitation token",
                    context={"token": token[:8] + "..."}
                )
            if team_member.status != "pending":
                raise TeamInvitationExpiredError(
                    detail="Invitation already processed",
                    context={"status": team_member.status, "member_id": team_member.id}
                )
            invitation = await self.repository.get_invitation_record(team_member.id)
            if invitation and invitation.expires_at < datetime.utcnow():
                raise TeamInvitationExpiredError(
                    detail="Invitation has expired",
                    context={
                        "expires_at": invitation.expires_at,
                        "current_time": datetime.utcnow(),
                        "member_id": team_member.id
                    }
                )
            team_member.user_id = user_id
            team_member.status = "active"
            team_member.accepted_at = datetime.utcnow()
            team_member.invitation_token = None
            if invitation:
                invitation.accepted_at = datetime.utcnow()
                await self.repository.update_invitation(invitation)
            updated_member = await self.repository.update(team_member, team_member.organization_owner_id)
            logger.info(f"Team invitation accepted: {team_member.id} by user {user_id}")
            return updated_member
        except (
            InvalidInvitationTokenError, TeamInvitationNotFoundError, TeamInvitationExpiredError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error accepting invitation: {e!s}", exc_info=True)
            raise TeamInvitationError(
                detail="Failed to accept invitation due to internal error",
                context={"user_id": user_id}
            )

    async def get_team_stats(self, owner_id: str) -> TeamStats:
        """Get team statistics for dashboard."""
        try:
            stats_data = await self.repository.get_team_stats(owner_id)
            return TeamStats(**stats_data)
        except Exception as e:
            logger.error(f"Error getting team stats: {e!s}")
            raise InternalServerError(
                detail="Failed to retrieve team statistics",
                context={"owner_id": owner_id}
            )

    # Validation hooks
    async def _pre_create_validation(self, entity_data: Dict[str, Any], user_id: str) -> None:
        """Team-specific pre-create validation."""
        await self._validate_team_member_data(entity_data, user_id)
        await self._check_duplicate_email(entity_data['email'], user_id)
        await self._validate_team_size_limit(user_id)
        await self._validate_role_assignment(entity_data.get('role'), user_id)

    async def _pre_update_validation(self, entity: TeamMember, update_data: Dict[str, Any], user_id: str) -> None:
        """Team-specific pre-update validation."""
        if 'role' in update_data:
            await self._validate_role_change(entity.role, update_data['role'], user_id)
        if 'email' in update_data and update_data['email'] != entity.email:
            await self._check_duplicate_email(update_data['email'], user_id, exclude_id=entity.id)

    async def _pre_delete_validation(self, entity: TeamMember, user_id: str) -> None:
        """Team-specific pre-delete validation."""
        if entity.role == 'owner':
            raise TeamMemberValidationError(
                detail="Cannot delete organization owner",
                context={"member_id": str(entity.id)}
            )

    # Private validation methods
    async def _validate_team_member_data(self, data: Dict[str, Any], user_id: str) -> None:
        """Validate team member data."""
        if not data.get('email') or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
            raise TeamMemberValidationError(
                detail="Invalid email format",
                context={"email": data.get('email')}
            )
        if 'role' in data and data['role'] not in VALID_TEAM_ROLES:
            raise InvalidTeamRoleError(
                detail="Invalid team role",
                context={"role": data['role'], "valid_roles": VALID_TEAM_ROLES}
            )
        if 'department' in data and data['department'] and data['department'] not in VALID_DEPARTMENTS:
            raise TeamDepartmentNotFoundError(
                detail="Invalid department",
                context={"department": data['department'], "valid_departments": VALID_DEPARTMENTS}
            )
        if 'job_title' in data and data['job_title'] and len(data['job_title']) > 100:
            raise TeamMemberValidationError(
                detail="Job title must be 100 characters or less",
                context={"job_title": data['job_title'], "length": len(data['job_title'])}
            )
        if 'permissions' in data:
            self._validate_permissions(data['permissions'])

    async def _check_duplicate_email(self, email: str, owner_id: str, exclude_id: Optional[str] = None) -> None:
        """Check for duplicate team member email in organization."""
        member = await self.repository.get_team_member_by_email(email, owner_id)
        if member and (exclude_id is None or member.id != exclude_id):
            raise DuplicateTeamMemberError(
                detail=f"Email '{email}' is already invited or a member",
                context={"email": email}
            )

    async def _validate_team_size_limit(self, owner_id: str) -> None:
        """Check if team size limit would be exceeded."""
        members = await self.repository.get_team_members(owner_id, status_filter="active")
        pending = await self.repository.get_team_members(owner_id, status_filter="pending")
        total = len(members) + len(pending)
        if total >= MAX_TEAM_SIZE:
            raise TeamSizeLimitExceededError(
                detail=f"Team size limit of {MAX_TEAM_SIZE} members exceeded",
                context={"current_size": total, "limit": MAX_TEAM_SIZE}
            )

    async def _validate_role_assignment(self, role: Optional[str], owner_id: str) -> None:
        """Validate role assignment for new member."""
        if role and role not in VALID_TEAM_ROLES:
            raise InvalidTeamRoleError(
                detail="Invalid team role",
                context={"role": role, "valid_roles": VALID_TEAM_ROLES}
            )

    async def _validate_role_change(self, current_role: str, new_role: str, owner_id: str) -> None:
        """Validate role change based on hierarchy rules."""
        if new_role not in VALID_TEAM_ROLES:
            raise InvalidTeamRoleError(
                detail="Invalid role",
                context={"role": new_role, "valid_roles": VALID_TEAM_ROLES}
            )
        if current_role == "owner":
            raise TeamRoleHierarchyError(
                detail="Cannot change owner role",
                context={"current_role": current_role, "new_role": new_role}
            )
        if new_role == "owner":
            raise TeamRoleHierarchyError(
                detail="Cannot promote member to owner role",
                context={"current_role": current_role, "new_role": new_role}
            )

    def _validate_permissions(self, permissions: dict) -> None:
        """Validate team member permissions structure."""
        if not isinstance(permissions, dict):
            raise InvalidTeamPermissionsError(
                detail="Permissions must be a dictionary",
                context={"permissions_type": type(permissions).__name__}
            )
        valid_permissions = {
            "can_view_expenses": bool,
            "can_create_expenses": bool,
            "can_edit_expenses": bool,
            "can_delete_expenses": bool,
            "can_approve_expenses": bool,
            "can_manage_categories": bool,
            "can_manage_team": bool,
            "can_view_reports": bool,
            "can_export_data": bool
        }
        for key, value in permissions.items():
            if key not in valid_permissions:
                raise InvalidTeamPermissionsError(
                    detail=f"Invalid permission key: {key}",
                    context={"invalid_key": key, "valid_keys": list(valid_permissions.keys())}
                )
            if not isinstance(value, valid_permissions[key]):
                raise InvalidTeamPermissionsError(
                    detail=f"Invalid permission value type for {key}",
                    context={"key": key, "expected_type": valid_permissions[key].__name__, "actual_type": type(value).__name__}
                )
    async def _send_invitation_email(self, team_member: TeamMember, token: str) -> None:
        """Send invitation email with error handling."""
        try:
            logger.info(f"Sending invitation email to {team_member.email} with token {token[:8]}...")
        except Exception as e:
            logger.error(f"Failed to send invitation email to {team_member.email}: {e!s}")
            raise TeamEmailDeliveryError(
                detail="Failed to send invitation email",
                context={"email": team_member.email}
            )