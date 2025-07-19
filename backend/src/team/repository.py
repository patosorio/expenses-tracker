from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select
from typing import Optional, List
import uuid
import secrets
from datetime import datetime, timedelta

from .models import TeamMember, TeamInvitation
from .exceptions import (
    TeamMemberNotFoundError, TeamInvitationNotFoundError,
    TeamValidationError, TeamInvitationError
)

class TeamRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Team Member Repository Methods
    async def get_team_members(
        self,
        owner_id: str,
        status_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        department_filter: Optional[str] = None
    ) -> List[TeamMember]:
        """Get team members for organization"""
        query = select(TeamMember).where(
            TeamMember.organization_owner_id == owner_id
        )
        
        if status_filter:
            query = query.where(TeamMember.status == status_filter)
        
        if role_filter:
            query = query.where(TeamMember.role == role_filter)
        
        if department_filter:
            query = query.where(TeamMember.department == department_filter)
        
        query = query.order_by(TeamMember.invited_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_team_member_by_id(self, member_id: str, owner_id: str) -> Optional[TeamMember]:
        """Get specific team member by ID"""
        result = await self.db.execute(
            select(TeamMember).where(
                and_(
                    TeamMember.id == member_id,
                    TeamMember.organization_owner_id == owner_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_team_member_by_email(self, email: str, owner_id: str) -> Optional[TeamMember]:
        """Get team member by email"""
        result = await self.db.execute(
            select(TeamMember).where(
                and_(
                    TeamMember.email == email,
                    TeamMember.organization_owner_id == owner_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_team_member(self, team_member: TeamMember) -> TeamMember:
        """Create new team member"""
        try:
            self.db.add(team_member)
            await self.db.commit()
            await self.db.refresh(team_member)
            return team_member
        except Exception as e:
            await self.db.rollback()
            raise TeamValidationError(f"Failed to create team member: {str(e)}")
    
    async def update_team_member(self, team_member: TeamMember) -> TeamMember:
        """Update team member"""
        try:
            await self.db.commit()
            await self.db.refresh(team_member)
            return team_member
        except Exception as e:
            await self.db.rollback()
            raise TeamValidationError(f"Failed to update team member: {str(e)}")
    
    async def delete_team_member(self, team_member: TeamMember) -> bool:
        """Soft delete team member"""
        try:
            team_member.status = "inactive"
            team_member.deactivated_at = datetime.utcnow()
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise TeamValidationError(f"Failed to delete team member: {str(e)}")
    
    # Team Invitation Repository Methods
    async def get_invitation_by_token(self, token: str) -> Optional[TeamMember]:
        """Get team member by invitation token"""
        result = await self.db.execute(
            select(TeamMember).where(TeamMember.invitation_token == token)
        )
        return result.scalar_one_or_none()
    
    async def get_invitation_record(self, team_member_id: str) -> Optional[TeamInvitation]:
        """Get invitation record by team member ID"""
        result = await self.db.execute(
            select(TeamInvitation).where(TeamInvitation.team_member_id == team_member_id)
        )
        return result.scalar_one_or_none()
    
    async def create_invitation(self, invitation: TeamInvitation) -> TeamInvitation:
        """Create new invitation record"""
        try:
            self.db.add(invitation)
            await self.db.commit()
            await self.db.refresh(invitation)
            return invitation
        except Exception as e:
            await self.db.rollback()
            raise TeamInvitationError(f"Failed to create invitation: {str(e)}")
    
    async def update_invitation(self, invitation: TeamInvitation) -> TeamInvitation:
        """Update invitation record"""
        try:
            await self.db.commit()
            await self.db.refresh(invitation)
            return invitation
        except Exception as e:
            await self.db.rollback()
            raise TeamInvitationError(f"Failed to update invitation: {str(e)}")
    
    # Statistics Repository Methods
    async def get_team_stats(self, owner_id: str) -> dict:
        """Get team statistics"""
        # Basic counts
        total_result = await self.db.execute(
            select(func.count(TeamMember.id)).where(TeamMember.organization_owner_id == owner_id)
        )
        total_members = total_result.scalar()
        
        active_result = await self.db.execute(
            select(func.count(TeamMember.id)).where(
                and_(
                    TeamMember.organization_owner_id == owner_id,
                    TeamMember.status == "active"
                )
            )
        )
        active_members = active_result.scalar()
        
        pending_result = await self.db.execute(
            select(func.count(TeamMember.id)).where(
                and_(
                    TeamMember.organization_owner_id == owner_id,
                    TeamMember.status == "pending"
                )
            )
        )
        pending_invitations = pending_result.scalar()
        
        # Members by role
        role_result = await self.db.execute(
            select(TeamMember.role, func.count(TeamMember.id))
            .where(TeamMember.organization_owner_id == owner_id)
            .group_by(TeamMember.role)
        )
        role_counts = dict(role_result.all())
        
        # Members by department
        dept_result = await self.db.execute(
            select(TeamMember.department, func.count(TeamMember.id))
            .where(
                and_(
                    TeamMember.organization_owner_id == owner_id,
                    TeamMember.department.isnot(None)
                )
            )
            .group_by(TeamMember.department)
        )
        department_counts = dict(dept_result.all())
        
        return {
            'total_members': total_members,
            'active_members': active_members,
            'pending_invitations': pending_invitations,
            'members_by_role': role_counts,
            'members_by_department': department_counts
        } 