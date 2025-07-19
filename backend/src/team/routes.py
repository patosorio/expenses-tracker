from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from .models import TeamMember, TeamInvitation
from .schemas import (
    TeamMemberResponse, TeamMemberInvite, TeamMemberUpdate,
    TeamInvitationResponse, TeamInvitationAccept, TeamStats
)
from .service import TeamService
from ..auth.dependencies import get_current_user
from ..users.models import User
from ..core.database import get_db
from .exceptions import (
    TeamMemberNotFoundError, TeamInvitationNotFoundError,
    TeamInvitationExpiredError, DuplicateTeamMemberError
)

router = APIRouter()

# Team Member Routes
@router.get("/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    status: Optional[str] = Query(None, description="Filter by status"),
    role: Optional[str] = Query(None, description="Filter by role"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team members"""
    try:
        team_service = TeamService(db)
        members = await team_service.get_team_members(
            owner_id=current_user.id,
            status_filter=status,
            role_filter=role,
            department_filter=department
        )
        return members
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team members: {str(e)}"
        )

@router.get("/members/{member_id}", response_model=TeamMemberResponse)
async def get_team_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific team member"""
    try:
        team_service = TeamService(db)
        member = await team_service.get_team_member(member_id, current_user.id)
        return member
    except TeamMemberNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team member: {str(e)}"
        )

@router.post("/invite", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_team_member(
    invitation_data: TeamMemberInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite team member"""
    try:
        team_service = TeamService(db)
        member = await team_service.invite_team_member(
            owner_id=current_user.id,
            invitation_data=invitation_data
        )
        return member
    except DuplicateTeamMemberError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite team member: {str(e)}"
        )

@router.put("/members/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: str,
    update_data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update team member"""
    try:
        team_service = TeamService(db)
        member = await team_service.update_team_member(
            member_id, current_user.id, update_data
        )
        return member
    except TeamMemberNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team member: {str(e)}"
        )

@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove team member"""
    try:
        team_service = TeamService(db)
        await team_service.remove_team_member(member_id, current_user.id)
    except TeamMemberNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove team member: {str(e)}"
        )

# Team Invitation Routes
@router.post("/invitations/accept", response_model=TeamMemberResponse)
async def accept_team_invitation(
    invitation_data: TeamInvitationAccept,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept team invitation"""
    try:
        team_service = TeamService(db)
        member = await team_service.accept_invitation(
            invitation_data.token, current_user.id
        )
        return member
    except (TeamInvitationNotFoundError, TeamInvitationExpiredError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept invitation: {str(e)}"
        )

# Team Statistics Routes
@router.get("/stats", response_model=TeamStats)
async def get_team_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team statistics"""
    try:
        team_service = TeamService(db)
        stats = await team_service.get_team_stats(current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team statistics: {str(e)}"
        ) 