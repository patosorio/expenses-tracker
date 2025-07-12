from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

class TeamMemberBase(BaseModel):
    email: EmailStr
    role: Literal["admin", "manager", "user", "viewer"] = "user"
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    permissions: Optional[Dict[str, Any]] = None

class TeamMemberInvite(TeamMemberBase):
    """Schema for inviting a team member"""
    pass

class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member"""
    role: Optional[Literal["admin", "manager", "user", "viewer"]] = None
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    permissions: Optional[Dict[str, Any]] = None
    status: Optional[Literal["active", "inactive", "suspended"]] = None

class TeamMemberResponse(TeamMemberBase):
    id: str
    organization_owner_id: str
    user_id: Optional[str] = None
    status: str
    invited_at: datetime
    accepted_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TeamInvitationBase(BaseModel):
    sent_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None

class TeamInvitationResponse(TeamInvitationBase):
    id: str
    team_member_id: str
    
    class Config:
        from_attributes = True

class TeamInvitationAccept(BaseModel):
    """Schema for accepting a team invitation"""
    token: str

class TeamStats(BaseModel):
    """Schema for team statistics"""
    total_members: int
    active_members: int
    pending_invitations: int
    members_by_role: Dict[str, int]
    members_by_department: Dict[str, int] 