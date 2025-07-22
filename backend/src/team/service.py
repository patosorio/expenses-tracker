from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid
import secrets
import re
from datetime import datetime, timedelta
import logging

from .models import TeamMember, TeamInvitation
from .repository import TeamRepository
from .schemas import TeamMemberInvite, TeamMemberUpdate, TeamStats
from .exceptions import *
from ..core.shared.exceptions import ValidationError, InternalServerError

logger = logging.getLogger(__name__)

# Business constants
MAX_TEAM_SIZE = 100
INVITATION_EXPIRY_DAYS = 7
VALID_TEAM_ROLES = ["owner", "admin", "manager", "member", "viewer"]
VALID_DEPARTMENTS = ["finance", "operations", "sales", "marketing", "hr", "it", "other"]


class TeamService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.team_repo = TeamRepository(db)
    
    async def get_team_members(
        self,
        owner_id: str,
        status_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        department_filter: Optional[str] = None
    ) -> List[TeamMember]:
        """Get team members for organization with validation."""
        try:
            # Validate filters
            if status_filter and status_filter not in ["active", "pending", "deactivated"]:
                raise TeamValidationError(
                    detail="Invalid status filter",
                    context={"status_filter": status_filter, "valid_statuses": ["active", "pending", "deactivated"]}
                )
            
            if role_filter and role_filter not in VALID_TEAM_ROLES:
                raise InvalidTeamRoleError(
                    detail="Invalid role filter",
                    context={"role_filter": role_filter, "valid_roles": VALID_TEAM_ROLES}
                )
            
            if department_filter and department_filter not in VALID_DEPARTMENTS:
                raise TeamDepartmentNotFoundError(
                    detail="Invalid department filter",
                    context={"department_filter": department_filter, "valid_departments": VALID_DEPARTMENTS}
                )
            
            return await self.team_repo.get_team_members(owner_id, status_filter, role_filter, department_filter)
            
        except (TeamValidationError, InvalidTeamRoleError, TeamDepartmentNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error getting team members for owner {owner_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve team members",
                context={"owner_id": owner_id, "original_error": str(e)}
            )
    
    async def get_team_member(self, member_id: str, owner_id: str) -> TeamMember:
        """Get specific team member with validation."""
        try:
            member = await self.team_repo.get_team_member_by_id(member_id, owner_id)
            
            if not member:
                raise TeamMemberNotFoundError(
                    detail=f"Team member with ID {member_id} not found",
                    context={"member_id": member_id, "owner_id": owner_id}
                )
            
            return member
            
        except TeamMemberNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting team member {member_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve team member",
                context={"member_id": member_id, "owner_id": owner_id, "original_error": str(e)}
            )
    
    async def invite_team_member(
        self,
        owner_id: str,
        invitation_data: TeamMemberInvite
    ) -> TeamMember:
        """Invite new team member with comprehensive validation."""
        try:
            # Validate invitation data
            await self._validate_invitation_data(invitation_data, owner_id)
            
            # Check team size limit
            await self._check_team_size_limit(owner_id)
            
            # Check if user is already invited or active
            existing = await self.team_repo.get_team_member_by_email(invitation_data.email, owner_id)
            
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
            
            # Generate secure invitation token
            invitation_token = secrets.token_urlsafe(32)
            
            # Create team member record
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
            
            # Create team member
            team_member = await self.team_repo.create_team_member(team_member)
            
            # Create invitation record
            invitation = TeamInvitation(
                id=str(uuid.uuid4()),
                team_member_id=team_member.id,
                expires_at=datetime.utcnow() + timedelta(days=INVITATION_EXPIRY_DAYS)
            )
            
            await self.team_repo.create_invitation(invitation)
            
            # Send invitation email
            try:
                await self._send_invitation_email(team_member, invitation_token)
            except Exception as e:
                logger.warning(f"Failed to send invitation email: {str(e)}")
                # Don't fail the invitation if email fails
            
            logger.info(f"Team member invited successfully: {team_member.id} for owner {owner_id}")
            return team_member
            
        except (
            TeamValidationError, DuplicateTeamMemberError, InvalidTeamRoleError,
            InvalidTeamPermissionsError, TeamSizeLimitExceededError, TeamMemberValidationError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error inviting team member for owner {owner_id}: {str(e)}", exc_info=True)
            raise TeamInvitationError(
                detail="Failed to create team invitation due to internal error",
                context={"owner_id": owner_id, "email": invitation_data.email, "original_error": str(e)}
            )
    
    async def update_team_member(
        self,
        member_id: str,
        owner_id: str,
        update_data: TeamMemberUpdate
    ) -> TeamMember:
        """Update team member information with validation."""
        try:
            # Get existing team member
            member = await self.get_team_member(member_id, owner_id)
            
            # Validate update data
            update_fields = update_data.model_dump(exclude_unset=True)
            if not update_fields:
                raise TeamMemberValidationError(
                    detail="No valid fields provided for update",
                    context={"member_id": member_id, "owner_id": owner_id}
                )
            
            # Validate role change
            if 'role' in update_fields:
                await self._validate_role_change(member, update_fields['role'], owner_id)
            
            # Validate department
            if 'department' in update_fields and update_fields['department'] not in VALID_DEPARTMENTS:
                raise TeamDepartmentNotFoundError(
                    detail="Invalid department",
                    context={"department": update_fields['department'], "valid_departments": VALID_DEPARTMENTS}
                )
            
            # Validate permissions
            if 'permissions' in update_fields:
                self._validate_permissions(update_fields['permissions'])
            
            # Apply updates
            for field, value in update_fields.items():
                setattr(member, field, value)
            
            updated_member = await self.team_repo.update_team_member(member)
            logger.info(f"Team member updated successfully: {member_id} for owner {owner_id}")
            return updated_member
            
        except (
            TeamMemberNotFoundError, TeamMemberValidationError, InvalidTeamRoleError,
            InvalidTeamPermissionsError, TeamDepartmentNotFoundError, TeamRoleHierarchyError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating team member {member_id}: {str(e)}", exc_info=True)
            raise TeamMemberUpdateError(
                detail="Failed to update team member due to internal error",
                context={"member_id": member_id, "owner_id": owner_id, "original_error": str(e)}
            )
    
    async def accept_invitation(self, token: str, user_id: str) -> TeamMember:
        """Accept team invitation with comprehensive validation."""
        try:
            # Validate token format
            if not token or len(token) < 20:
                raise InvalidInvitationTokenError(
                    detail="Invalid invitation token format",
                    context={"token_length": len(token) if token else 0}
                )
            
            # Get team member by token
            team_member = await self.team_repo.get_invitation_by_token(token)
            
            if not team_member:
                raise TeamInvitationNotFoundError(
                    detail="Invalid invitation token",
                    context={"token": token[:8] + "..."}  # Log partial token for debugging
                )
            
            if team_member.status != "pending":
                raise TeamInvitationExpiredError(
                    detail="Invitation already processed",
                    context={"status": team_member.status, "member_id": team_member.id}
                )
            
            # Check if invitation expired
            invitation = await self.team_repo.get_invitation_record(team_member.id)
            
            if invitation and invitation.expires_at < datetime.utcnow():
                raise TeamInvitationExpiredError(
                    detail="Invitation has expired",
                    context={
                        "expires_at": invitation.expires_at,
                        "current_time": datetime.utcnow(),
                        "member_id": team_member.id
                    }
                )
            
            # Accept invitation
            team_member.user_id = user_id
            team_member.status = "active"
            team_member.accepted_at = datetime.utcnow()
            team_member.invitation_token = None
            
            if invitation:
                invitation.accepted_at = datetime.utcnow()
                await self.team_repo.update_invitation(invitation)
            
            updated_member = await self.team_repo.update_team_member(team_member)
            logger.info(f"Team invitation accepted: {team_member.id} by user {user_id}")
            return updated_member
            
        except (
            InvalidInvitationTokenError, TeamInvitationNotFoundError, TeamInvitationExpiredError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error accepting invitation: {str(e)}", exc_info=True)
            raise TeamInvitationError(
                detail="Failed to accept invitation due to internal error",
                context={"user_id": user_id, "original_error": str(e)}
            )
    
    async def remove_team_member(
        self,
        member_id: str,
        owner_id: str,
        requester_id: str
    ) -> bool:
        """Remove team member with permission validation."""
        try:
            # Get team member
            member = await self.get_team_member(member_id, owner_id)
            
            # Business rule: Cannot remove yourself if you're the owner
            if member.user_id == requester_id and member.role == "owner":
                raise TeamMemberSelfRemovalError(
                    detail="Team owner cannot remove themselves",
                    context={"member_id": member_id, "requester_id": requester_id}
                )
            
            # Business rule: Check permissions for removal
            await self._validate_removal_permissions(member, requester_id, owner_id)
            
            # Perform soft delete
            result = await self.team_repo.delete_team_member(member)
            logger.info(f"Team member removed successfully: {member_id} by {requester_id}")
            return result
            
        except (
            TeamMemberNotFoundError, TeamMemberSelfRemovalError, InsufficientTeamPermissionsError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error removing team member {member_id}: {str(e)}", exc_info=True)
            raise TeamMemberDeleteError(
                detail="Failed to remove team member due to internal error",
                context={"member_id": member_id, "owner_id": owner_id, "original_error": str(e)}
            )
    
    async def get_team_stats(self, owner_id: str) -> TeamStats:
        """Get team statistics with error handling."""
        try:
            stats_data = await self.team_repo.get_team_stats(owner_id)
            return TeamStats(**stats_data)
        except Exception as e:
            logger.error(f"Error getting team stats for owner {owner_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve team statistics",
                context={"owner_id": owner_id, "original_error": str(e)}
            )
    
    # Private helper methods for validation
    
    async def _validate_invitation_data(self, invitation_data: TeamMemberInvite, owner_id: str) -> None:
        """Validate invitation data comprehensively."""
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, invitation_data.email):
            raise TeamMemberValidationError(
                detail="Invalid email format",
                context={"email": invitation_data.email}
            )
        
        # Validate role
        if invitation_data.role not in VALID_TEAM_ROLES:
            raise InvalidTeamRoleError(
                detail="Invalid team role",
                context={"role": invitation_data.role, "valid_roles": VALID_TEAM_ROLES}
            )
        
        # Validate department
        if invitation_data.department and invitation_data.department not in VALID_DEPARTMENTS:
            raise TeamDepartmentNotFoundError(
                detail="Invalid department",
                context={"department": invitation_data.department, "valid_departments": VALID_DEPARTMENTS}
            )
        
        # Validate job title length
        if invitation_data.job_title and len(invitation_data.job_title) > 100:
            raise TeamMemberValidationError(
                detail="Job title must be 100 characters or less",
                context={"job_title": invitation_data.job_title, "length": len(invitation_data.job_title)}
            )
        
        # Validate permissions
        if invitation_data.permissions:
            self._validate_permissions(invitation_data.permissions)
    
    def _validate_permissions(self, permissions: dict) -> None:
        """Validate team member permissions structure."""
        if not isinstance(permissions, dict):
            raise InvalidTeamPermissionsError(
                detail="Permissions must be a dictionary",
                context={"permissions_type": type(permissions).__name__}
            )
        
        # Define valid permission keys and values
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
    
    async def _check_team_size_limit(self, owner_id: str) -> None:
        """Check if team size limit would be exceeded."""
        try:
            current_members = await self.team_repo.get_team_members(owner_id, status_filter="active")
            pending_members = await self.team_repo.get_team_members(owner_id, status_filter="pending")
            
            total_members = len(current_members) + len(pending_members)
            
            if total_members >= MAX_TEAM_SIZE:
                raise TeamSizeLimitExceededError(
                    detail=f"Team size limit of {MAX_TEAM_SIZE} members exceeded",
                    context={"current_size": total_members, "limit": MAX_TEAM_SIZE}
                )
        except TeamSizeLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Error checking team size limit: {str(e)}")
            raise InternalServerError(
                detail="Failed to validate team size limit",
                context={"owner_id": owner_id, "original_error": str(e)}
            )
    
    async def _validate_role_change(self, member: TeamMember, new_role: str, owner_id: str) -> None:
        """Validate role change based on hierarchy rules."""
        if new_role not in VALID_TEAM_ROLES:
            raise InvalidTeamRoleError(
                detail="Invalid role",
                context={"role": new_role, "valid_roles": VALID_TEAM_ROLES}
            )
        
        # Business rule: Cannot change owner role
        if member.role == "owner":
            raise TeamRoleHierarchyError(
                detail="Cannot change owner role",
                context={"current_role": member.role, "new_role": new_role}
            )
        
        # Business rule: Cannot promote to owner
        if new_role == "owner":
            raise TeamRoleHierarchyError(
                detail="Cannot promote member to owner role",
                context={"current_role": member.role, "new_role": new_role}
            )
    
    async def _validate_removal_permissions(self, member: TeamMember, requester_id: str, owner_id: str) -> None:
        """Validate permissions for removing a team member."""
        # Get requester's role
        requester = await self.team_repo.get_team_member_by_user_id(requester_id, owner_id)
        
        if not requester:
            raise InsufficientTeamPermissionsError(
                detail="Requester is not a team member",
                context={"requester_id": requester_id, "owner_id": owner_id}
            )
        
        # Business rule: Only owners and admins can remove members
        if requester.role not in ["owner", "admin"]:
            raise InsufficientTeamPermissionsError(
                detail="Insufficient permissions to remove team members",
                context={"requester_role": requester.role, "required_roles": ["owner", "admin"]}
            )
        
        # Business rule: Admins cannot remove other admins or owners
        if requester.role == "admin" and member.role in ["owner", "admin"]:
            raise InsufficientTeamPermissionsError(
                detail="Admins cannot remove owners or other admins",
                context={"requester_role": requester.role, "target_role": member.role}
            )
    
    async def _send_invitation_email(self, team_member: TeamMember, token: str) -> None:
        """Send invitation email with error handling."""
        try:
            # TODO: Implement actual email service integration
            # For now, just log the invitation
            logger.info(f"Sending invitation email to {team_member.email} with token {token[:8]}...")
            
            # Placeholder email service
            # await email_service.send_team_invitation(
            #     to_email=team_member.email,
            #     invitation_token=token,
            #     inviter_name=...,
            #     organization_name=...
            # )
            
        except Exception as e:
            logger.error(f"Failed to send invitation email to {team_member.email}: {str(e)}")
            raise TeamEmailDeliveryError(
                detail="Failed to send invitation email",
                context={"email": team_member.email, "original_error": str(e)}
            )