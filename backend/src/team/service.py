from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid
import secrets
from datetime import datetime, timedelta
import logging

from .models import TeamMember, TeamInvitation
from .repository import TeamRepository
from .schemas import TeamMemberInvite, TeamMemberUpdate, TeamStats
from .exceptions import (
    TeamMemberNotFoundError, TeamInvitationNotFoundError, 
    TeamInvitationExpiredError, DuplicateTeamMemberError,
    TeamValidationError, TeamInvitationError
)

logger = logging.getLogger(__name__)

class TeamService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.team_repo = TeamRepository(self.db)
    
    async def get_team_members(
        self,
        owner_id: str,
        status_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        department_filter: Optional[str] = None
    ) -> List[TeamMember]:
        """Get team members for organization"""
        # Delegate to repository for data access
        return await self.team_repo.get_team_members(owner_id, status_filter, role_filter, department_filter)
    
    async def get_team_member(
        self,
        member_id: str,
        owner_id: str
    ) -> TeamMember:
        """Get specific team member"""
        member = await self.team_repo.get_team_member_by_id(member_id, owner_id)
        
        if not member:
            raise TeamMemberNotFoundError("Team member not found")
        
        return member
    
    async def invite_team_member(
        self,
        owner_id: str,
        invitation_data: TeamMemberInvite
    ) -> TeamMember:
        """Invite new team member"""
        
        # Business logic: Check if already invited or active
        existing = await self.team_repo.get_team_member_by_email(invitation_data.email, owner_id)
        
        if existing and existing.status == "active":
            raise DuplicateTeamMemberError("User is already a team member")
        
        if existing and existing.status == "pending":
            raise DuplicateTeamMemberError("Invitation already sent to this email")
        
        # Business logic: Generate invitation token
        invitation_token = secrets.token_urlsafe(32)
        
        # Business logic: Create team member record
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
        
        # Delegate to repository for data access
        team_member = await self.team_repo.create_team_member(team_member)
        
        # Business logic: Create invitation record
        invitation = TeamInvitation(
            id=str(uuid.uuid4()),
            team_member_id=team_member.id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        await self.team_repo.create_invitation(invitation)
        
        # TODO: Send invitation email
        await self._send_invitation_email(team_member, invitation_token)
        
        return team_member
    
    async def update_team_member(
        self,
        member_id: str,
        owner_id: str,
        update_data: TeamMemberUpdate
    ) -> TeamMember:
        """Update team member information"""
        member = await self.get_team_member(member_id, owner_id)
        
        # Update only provided fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(member, field, value)
        
        # Delegate to repository for data access
        return await self.team_repo.update_team_member(member)
    
    async def accept_invitation(self, token: str, user_id: str) -> TeamMember:
        """Accept team invitation"""
        team_member = await self.team_repo.get_invitation_by_token(token)
        
        if not team_member:
            raise TeamInvitationNotFoundError("Invalid invitation token")
        
        if team_member.status != "pending":
            raise TeamInvitationExpiredError("Invitation already processed")
        
        # Business logic: Check if invitation expired
        invitation = await self.team_repo.get_invitation_record(team_member.id)
        
        if invitation and invitation.expires_at < datetime.utcnow():
            raise TeamInvitationExpiredError("Invitation has expired")
        
        # Business logic: Accept invitation
        team_member.user_id = user_id
        team_member.status = "active"
        team_member.accepted_at = datetime.utcnow()
        team_member.invitation_token = None
        
        if invitation:
            invitation.accepted_at = datetime.utcnow()
            await self.team_repo.update_invitation(invitation)
        
        # Delegate to repository for data access
        return await self.team_repo.update_team_member(team_member)
    
    async def remove_team_member(
        self,
        member_id: str,
        owner_id: str
    ) -> bool:
        """Remove team member (soft delete)"""
        member = await self.get_team_member(member_id, owner_id)
        
        # Delegate to repository for data access
        return await self.team_repo.delete_team_member(member)
    
    async def get_team_stats(self, owner_id: str) -> TeamStats:
        """Get team statistics"""
        # Delegate to repository for data access
        stats_data = await self.team_repo.get_team_stats(owner_id)
        
        return TeamStats(**stats_data)
    
    async def _send_invitation_email(self, team_member: TeamMember, token: str):
        """Send invitation email (placeholder for email service)"""
        # TODO: Implement email sending
        print(f"Sending invitation email to {team_member.email} with token {token}")
        pass 