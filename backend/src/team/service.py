from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List
import uuid
import secrets
from datetime import datetime, timedelta

from src.team.models import TeamMember, TeamInvitation
from src.team.schemas import TeamMemberInvite, TeamMemberUpdate, TeamStats
from src.exceptions import (
    TeamMemberNotFoundError, TeamInvitationNotFoundError, 
    TeamInvitationExpiredError, DuplicateTeamMemberError
)

class TeamService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_team_members(
        self,
        owner_id: str,
        status_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        department_filter: Optional[str] = None
    ) -> List[TeamMember]:
        """Get team members for organization"""
        query = self.db.query(TeamMember).filter(
            TeamMember.organization_owner_id == owner_id
        )
        
        if status_filter:
            query = query.filter(TeamMember.status == status_filter)
        
        if role_filter:
            query = query.filter(TeamMember.role == role_filter)
        
        if department_filter:
            query = query.filter(TeamMember.department == department_filter)
        
        return query.order_by(TeamMember.invited_at.desc()).all()
    
    async def get_team_member(
        self,
        member_id: str,
        owner_id: str
    ) -> TeamMember:
        """Get specific team member"""
        member = self.db.query(TeamMember).filter(
            and_(
                TeamMember.id == member_id,
                TeamMember.organization_owner_id == owner_id
            )
        ).first()
        
        if not member:
            raise TeamMemberNotFoundError("Team member not found")
        
        return member
    
    async def invite_team_member(
        self,
        owner_id: str,
        invitation_data: TeamMemberInvite
    ) -> TeamMember:
        """Invite new team member"""
        
        # Check if already invited or active
        existing = self.db.query(TeamMember).filter(
            and_(
                TeamMember.organization_owner_id == owner_id,
                TeamMember.email == invitation_data.email
            )
        ).first()
        
        if existing and existing.status == "active":
            raise DuplicateTeamMemberError("User is already a team member")
        
        if existing and existing.status == "pending":
            raise DuplicateTeamMemberError("Invitation already sent to this email")
        
        # Generate invitation token
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
        
        self.db.add(team_member)
        
        # Create invitation record
        invitation = TeamInvitation(
            id=str(uuid.uuid4()),
            team_member_id=team_member.id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(team_member)
        
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
        
        self.db.commit()
        self.db.refresh(member)
        
        return member
    
    async def accept_invitation(self, token: str, user_id: str) -> TeamMember:
        """Accept team invitation"""
        team_member = self.db.query(TeamMember).filter(
            TeamMember.invitation_token == token
        ).first()
        
        if not team_member:
            raise TeamInvitationNotFoundError("Invalid invitation token")
        
        if team_member.status != "pending":
            raise TeamInvitationExpiredError("Invitation already processed")
        
        # Check if invitation expired
        invitation = self.db.query(TeamInvitation).filter(
            TeamInvitation.team_member_id == team_member.id
        ).first()
        
        if invitation and invitation.expires_at < datetime.utcnow():
            raise TeamInvitationExpiredError("Invitation has expired")
        
        # Accept invitation
        team_member.user_id = user_id
        team_member.status = "active"
        team_member.accepted_at = datetime.utcnow()
        team_member.invitation_token = None
        
        if invitation:
            invitation.accepted_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(team_member)
        
        return team_member
    
    async def remove_team_member(
        self,
        member_id: str,
        owner_id: str
    ) -> bool:
        """Remove team member (soft delete)"""
        member = await self.get_team_member(member_id, owner_id)
        
        member.status = "inactive"
        member.deactivated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    async def get_team_stats(self, owner_id: str) -> TeamStats:
        """Get team statistics"""
        # Basic counts
        total_members = self.db.query(TeamMember).filter(
            TeamMember.organization_owner_id == owner_id
        ).count()
        
        active_members = self.db.query(TeamMember).filter(
            and_(
                TeamMember.organization_owner_id == owner_id,
                TeamMember.status == "active"
            )
        ).count()
        
        pending_invitations = self.db.query(TeamMember).filter(
            and_(
                TeamMember.organization_owner_id == owner_id,
                TeamMember.status == "pending"
            )
        ).count()
        
        # Members by role
        role_counts = dict(
            self.db.query(TeamMember.role, func.count(TeamMember.id))
            .filter(TeamMember.organization_owner_id == owner_id)
            .group_by(TeamMember.role)
            .all()
        )
        
        # Members by department
        department_counts = dict(
            self.db.query(TeamMember.department, func.count(TeamMember.id))
            .filter(
                and_(
                    TeamMember.organization_owner_id == owner_id,
                    TeamMember.department.isnot(None)
                )
            )
            .group_by(TeamMember.department)
            .all()
        )
        
        return TeamStats(
            total_members=total_members,
            active_members=active_members,
            pending_invitations=pending_invitations,
            members_by_role=role_counts,
            members_by_department=department_counts
        )
    
    async def _send_invitation_email(self, team_member: TeamMember, token: str):
        """Send invitation email (placeholder for email service)"""
        # TODO: Implement email sending
        print(f"Sending invitation email to {team_member.email} with token {token}")
        pass 