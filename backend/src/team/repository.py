from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select
from typing import Optional, List, Dict
from datetime import datetime
import logging

from .models import TeamMember, TeamInvitation
from ..core.shared.base_repository import BaseRepository
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)

class TeamRepository(BaseRepository[TeamMember]):
    """Repository for team data access operations extending BaseRepository."""
    def __init__(self, db: AsyncSession) -> None:
        """Initialize TeamRepository with database session."""
        super().__init__(db, TeamMember)

    async def get_team_members(
        self,
        owner_id: str,
        status_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        department_filter: Optional[str] = None
    ) -> List[TeamMember]:
        """Get team members for organization."""
        try:
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
            members = result.scalars().all()
            logger.info(f"Retrieved {len(members)} team members for owner {owner_id}")
            return list(members)
        except Exception as e:
            logger.error(f"Database error getting team members for owner {owner_id}: {e!s}")
            raise InternalServerError(
                detail="Database error while retrieving team members",
                context={"owner_id": owner_id}
            )

    async def get_team_member_by_id(self, member_id: str, owner_id: str) -> Optional[TeamMember]:
        """Get specific team member by ID."""
        try:
            result = await self.db.execute(
                select(TeamMember).where(
                    and_(
                        TeamMember.id == member_id,
                        TeamMember.organization_owner_id == owner_id
                    )
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                logger.warning(f"Team member {member_id} not found for owner {owner_id}")
                return None
            return member
        except Exception as e:
            logger.error(f"Database error getting team member {member_id}: {e!s}")
            raise InternalServerError(
                detail="Database error while retrieving team member",
                context={"member_id": member_id, "owner_id": owner_id}
            )

    async def get_team_member_by_email(self, email: str, owner_id: str) -> Optional[TeamMember]:
        """Get team member by email."""
        try:
            result = await self.db.execute(
                select(TeamMember).where(
                    and_(
                        TeamMember.email == email,
                        TeamMember.organization_owner_id == owner_id
                    )
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                logger.info(f"No team member found with email {email} for owner {owner_id}")
                return None
            return member
        except Exception as e:
            logger.error(f"Database error getting team member by email {email}: {e!s}")
            raise InternalServerError(
                detail="Database error while retrieving team member by email",
                context={"email": email, "owner_id": owner_id}
            )

    async def get_team_member_by_user_id(self, user_id: str, owner_id: str) -> Optional[TeamMember]:
        """Get team member by user ID."""
        try:
            result = await self.db.execute(
                select(TeamMember).where(
                    and_(
                        TeamMember.user_id == user_id,
                        TeamMember.organization_owner_id == owner_id
                    )
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                logger.info(f"No team member found with user_id {user_id} for owner {owner_id}")
                return None
            return member
        except Exception as e:
            logger.error(f"Database error getting team member by user_id {user_id}: {e!s}")
            raise InternalServerError(
                detail="Database error while retrieving team member by user ID",
                context={"user_id": user_id, "owner_id": owner_id}
            )

    async def get_invitation_by_token(self, token: str) -> Optional[TeamMember]:
        """Get team member by invitation token."""
        try:
            result = await self.db.execute(
                select(TeamMember).where(TeamMember.invitation_token == token)
            )
            member = result.scalar_one_or_none()
            if not member:
                logger.warning(f"No team member found with invitation token {token[:8]}...")
                return None
            return member
        except Exception as e:
            logger.error(f"Database error getting invitation by token: {e!s}")
            raise InternalServerError(
                detail="Database error while retrieving invitation",
                context={"token_preview": token[:8] + "..."}
            )

    async def get_invitation_record(self, team_member_id: str) -> Optional[TeamInvitation]:
        """Get invitation record by team member ID."""
        try:
            result = await self.db.execute(
                select(TeamInvitation).where(TeamInvitation.team_member_id == team_member_id)
            )
            invitation = result.scalar_one_or_none()
            if not invitation:
                logger.info(f"No invitation record found for team member {team_member_id}")
                return None
            return invitation
        except Exception as e:
            logger.error(f"Database error getting invitation record for member {team_member_id}: {e!s}")
            raise InternalServerError(
                detail="Database error while retrieving invitation record",
                context={"team_member_id": team_member_id}
            )

    async def get_team_stats(self, owner_id: str) -> Dict:
        """Get team statistics."""
        try:
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
            role_result = await self.db.execute(
                select(TeamMember.role, func.count(TeamMember.id))
                .where(TeamMember.organization_owner_id == owner_id)
                .group_by(TeamMember.role)
            )
            role_counts = dict(role_result.all())
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
            stats = {
                'total_members': total_members,
                'active_members': active_members,
                'pending_invitations': pending_invitations,
                'members_by_role': role_counts,
                'members_by_department': department_counts
            }
            logger.info(f"Retrieved team stats for owner {owner_id}: {total_members} total members")
            return stats
        except Exception as e:
            logger.error(f"Database error getting team stats for owner {owner_id}: {e!s}")
            raise InternalServerError(
                detail="Database error while retrieving team statistics",
                context={"owner_id": owner_id}
            )