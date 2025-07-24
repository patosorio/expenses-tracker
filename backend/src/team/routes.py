from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from .service import TeamService
from .schemas import (
    TeamMemberResponse, TeamMemberInvite, TeamMemberUpdate, 
    TeamMemberListResponse, TeamStats
)
from ..auth.dependencies import get_current_user
from ..users.models import User
from ..core.database import get_db
from ..core.shared.decorators import api_endpoint
from ..core.shared.pagination import create_legacy_team_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=TeamMemberListResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_team_members(
    status: Optional[str] = Query(None, description="Filter by member status"),
    role: Optional[str] = Query(None, description="Filter by member role"),
    department: Optional[str] = Query(None, description="Filter by department"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team members with filtering and pagination."""
    service = TeamService(db)
    filters = {"status": status, "role": role, "department": department}
    members, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters=filters
    )
    return create_legacy_team_response(members, total, skip, limit)


@router.post("/invite", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def invite_team_member(
    invitation_data: TeamMemberInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a new team member."""
    service = TeamService(db)
    member = await service.invite_team_member(current_user.id, invitation_data)
    return TeamMemberResponse.model_validate(member)


@router.post("/accept-invitation", response_model=TeamMemberResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def accept_invitation(
    token: str = Query(..., description="Invitation token from email"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept team invitation."""
    service = TeamService(db)
    member = await service.accept_invitation(token, current_user.id)
    return TeamMemberResponse.model_validate(member)


@router.get("/stats", response_model=TeamStats)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_team_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team statistics."""
    service = TeamService(db)
    return await service.get_team_stats(current_user.id)


@router.get("/{member_id}", response_model=TeamMemberResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_team_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific team member."""
    service = TeamService(db)
    member = await service.get_by_id(member_id, current_user.id)
    return TeamMemberResponse.model_validate(member)


@router.put("/{member_id}", response_model=TeamMemberResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_team_member(
    member_id: str,
    update_data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update team member information."""
    service = TeamService(db)
    member = await service.update_by_id(member_id, current_user.id, update_data.model_dump(exclude_unset=True))
    return TeamMemberResponse.model_validate(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def remove_team_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove team member."""
    service = TeamService(db)
    await service.delete_by_id(member_id, current_user.id)
    # No return needed for 204 status