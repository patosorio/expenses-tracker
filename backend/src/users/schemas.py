from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, computed_field, ConfigDict

from .models import UserRole, UserStatus


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
    
    model_config = ConfigDict(from_attributes=True)


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


# User Settings Schemas

class NotificationSettings(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    bill_reminders: bool = True
    weekly_reports: bool = False
    overdue_invoices: bool = True
    team_updates: bool = True
    marketing_emails: bool = False
    expense_summaries: bool = True
    budget_alerts: bool = True


class UserPreferences(BaseModel):
    currency: str = "EUR"
    date_format: str = "DD/MM/YYYY"
    time_format: str = "24h"
    week_start: str = "monday"
    theme: str = "system"
    fiscal_year_start: str = "01-01"
    default_export_format: str = "csv"
    include_attachments: bool = True


class UserSettingsResponse(BaseModel):
    id: str
    user_id: str
    # Preferences
    currency: str
    date_format: str
    time_format: str
    week_start: str
    theme: str
    fiscal_year_start: str
    default_export_format: str
    include_attachments: bool
    # Notifications
    email_notifications: bool
    push_notifications: bool
    bill_reminders: bool
    weekly_reports: bool
    overdue_invoices: bool
    team_updates: bool
    marketing_emails: bool
    expense_summaries: bool
    budget_alerts: bool
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserSettingsUpdate(BaseModel):
    # Preferences (all optional for partial updates)
    currency: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    week_start: Optional[str] = None
    theme: Optional[str] = None
    fiscal_year_start: Optional[str] = None
    default_export_format: Optional[str] = None
    include_attachments: Optional[bool] = None
    # Notifications (all optional)
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    bill_reminders: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    overdue_invoices: Optional[bool] = None
    team_updates: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    expense_summaries: Optional[bool] = None
    budget_alerts: Optional[bool] = None


class NotificationSettingsUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    bill_reminders: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    overdue_invoices: Optional[bool] = None
    team_updates: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    expense_summaries: Optional[bool] = None
    budget_alerts: Optional[bool] = None


class UserPreferencesUpdate(BaseModel):
    currency: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    week_start: Optional[str] = None
    theme: Optional[str] = None
    fiscal_year_start: Optional[str] = None
    default_export_format: Optional[str] = None
    include_attachments: Optional[bool] = None