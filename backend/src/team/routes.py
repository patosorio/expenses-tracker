from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging

from .service import TeamService
from .schemas import (
    TeamMemberResponse, TeamMemberInvite, TeamMemberUpdate, 
    TeamMemberListResponse, TeamStats, TeamInvitationResponse
)
# Exceptions are handled by global exception handler - no imports needed
from ..auth.dependencies import get_current_user
from ..users.models import User
from ..core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=TeamMemberListResponse)
async def get_team_members(
    status: Optional[str] = Query(None, description="Filter by member status"),
    role: Optional[str] = Query(None, description="Filter by member role"),
    department: Optional[str] = Query(None, description="Filter by department"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team members with filtering"""
    team_service = TeamService(db)
    members = await team_service.get_team_members(
        current_user.id,
        status_filter=status,
        role_filter=role,
        department_filter=department
    )
    
    # Simple pagination for team members list
    skip = (page - 1) * per_page
    paginated_members = members[skip:skip + per_page]
    
    return TeamMemberListResponse(
        members=[TeamMemberResponse.model_validate(member) for member in paginated_members],
        total=len(members),
        page=page,
        per_page=per_page,
        pages=(len(members) + per_page - 1) // per_page
    )


@router.post("/invite", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_team_member(
    invitation_data: TeamMemberInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a new team member"""
    team_service = TeamService(db)
    return await team_service.invite_team_member(current_user.id, invitation_data)


@router.post("/accept-invitation", response_model=TeamMemberResponse)
async def accept_invitation(
    token: str = Query(..., description="Invitation token from email"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept team invitation"""
    team_service = TeamService(db)
    return await team_service.accept_invitation(token, current_user.id)


@router.get("/stats", response_model=TeamStats)
async def get_team_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team statistics"""
    team_service = TeamService(db)
    return await team_service.get_team_stats(current_user.id)


@router.get("/{member_id}", response_model=TeamMemberResponse)
async def get_team_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific team member"""
    team_service = TeamService(db)
    return await team_service.get_team_member(member_id, current_user.id)


@router.put("/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: str,
    update_data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update team member information"""
    team_service = TeamService(db)
    return await team_service.update_team_member(member_id, current_user.id, update_data)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove team member"""
    team_service = TeamService(db)
    await team_service.remove_team_member(member_id, current_user.id, current_user.id)
    return {"message": "Team member removed successfully"}