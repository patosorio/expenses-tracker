from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, computed_field

from src.users.models import UserRole, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    timezone: str = "CET"
    language: str = "en"
    avatar_url: Optional[str] = None
    company: Optional[str] = None
    user_type: Literal['personal', 'business'] = 'personal'


class UserCreate(UserBase):
    firebase_uid: str
    is_verified: bool = False
    role: UserRole = UserRole.ADMIN
    status: UserStatus = UserStatus.ACTIVE


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    company: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: str
    firebase_uid: str
    is_verified: bool
    is_active: bool
    role: UserRole
    status: UserStatus
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int

class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    new_users_this_month: int
    verified_users: int
    users_by_role: dict[UserRole, int]
    users_by_status: dict[UserStatus, int]