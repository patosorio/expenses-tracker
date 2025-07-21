from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math
import logging

from .models import User, UserRole, UserStatus
from .schemas import (
    UserResponse,
    UserUpdate,
    UserListResponse,
    UserStatsResponse,
    UserCreate,
    UserSettingsResponse,
    UserSettingsUpdate,
    NotificationSettingsUpdate,
    UserPreferencesUpdate,
    NotificationSettings,
    UserPreferences
)
from .service import UserService
from ..auth.dependencies import get_current_user
from ..core.database import get_db

from .exceptions import (
    UserNotFoundError, UserAlreadyExistsError, InvalidUserDataError,
    AccountDeactivatedError
)
from core.exceptions import ValidationError, ForbiddenError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    user_service = UserService(db)
    created_user = await user_service.create_user(user_data)
    logger.info(f"User created successfully: {created_user.id}")
    return created_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user.id, user_update)
    logger.info(f"User profile updated successfully: {updated_user.id}")
    return updated_user


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get users with filtering and pagination (Admin/Manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise ForbiddenError(
            detail="Insufficient permissions to access user list",
            context={"required_roles": ["ADMIN", "MANAGER"], "user_role": current_user.role}
        )
    
    user_service = UserService(db)
    users, total = await user_service.get_users(
        skip=skip,
        limit=limit,
        role=role,
        status=status,
        search=search
    )
    
    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=math.ceil(total / limit)
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (Admin/Manager only or own profile)"""
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise ForbiddenError(
            detail="Insufficient permissions to access this user profile",
            context={"requested_user_id": user_id, "current_user_role": current_user.role}
        )
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    logger.info(f"User retrieved successfully: {user_id}")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user (Admin only or own profile)"""
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise ForbiddenError(
            detail="Insufficient permissions to update this user",
            context={"target_user_id": user_id, "current_user_role": current_user.role}
        )
    
    user_service = UserService(db)
    updated_user = await user_service.update_user(user_id, user_update)
    logger.info(f"User updated successfully: {user_id}")
    return updated_user


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError(
            detail="Insufficient permissions to deactivate user",
            context={"target_user_id": user_id, "current_user_role": current_user.role}
        )
    
    if current_user.id == user_id:
        raise ValidationError(
            detail="Cannot deactivate own account",
            context={"user_id": user_id}
        )
    
    user_service = UserService(db)
    await user_service.deactivate_user(user_id)
    return {"message": "User deactivated successfully", "user_id": user_id}


@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics (Admin/Manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise ForbiddenError(
            detail="Insufficient permissions to access user statistics",
            context={"required_roles": ["ADMIN", "MANAGER"], "user_role": current_user.role}
        )
    
    user_service = UserService(db)
    stats = await user_service.get_user_stats()
    logger.info("User statistics retrieved successfully")
    return stats

# User Settings Routes


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's settings and preferences"""
    user_service = UserService(db)
    settings = await user_service.get_user_settings(current_user.id)
    return settings


@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user settings and preferences"""
    user_service = UserService(db)
    updated_settings = await user_service.update_user_settings(current_user.id, settings_data)
    return updated_settings


@router.put("/me/settings/notifications", response_model=UserSettingsResponse)
async def update_notification_preferences(
    notification_data: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update notification preferences with specialized validation"""
    user_service = UserService(db)
    updated_settings = await user_service.update_notification_preferences(current_user.id, notification_data)
    return updated_settings


@router.put("/me/settings/preferences", response_model=UserSettingsResponse)
async def update_display_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update display and UI preferences with specialized validation"""
    user_service = UserService(db)
    updated_settings = await user_service.update_display_preferences(current_user.id, preferences_data)
    return updated_settings


@router.post("/me/settings/reset", response_model=UserSettingsResponse)
async def reset_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset user settings to default values"""
    user_service = UserService(db)
    reset_settings = await user_service.reset_settings_to_default(current_user.id)
    return reset_settings

# Convenience endpoints for specific setting groups


@router.get("/me/settings/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get only user preferences (for quick access)"""
    user_service = UserService(db)
    settings = await user_service.get_user_settings(current_user.id)
    
    return UserPreferences(
        currency=settings.currency,
        date_format=settings.date_format,
        time_format=settings.time_format,
        week_start=settings.week_start,
        theme=settings.theme,
        fiscal_year_start=settings.fiscal_year_start,
        default_export_format=settings.default_export_format,
        include_attachments=settings.include_attachments
    )


@router.get("/me/settings/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get only notification settings (for quick access)"""
    user_service = UserService(db)
    settings = await user_service.get_user_settings(current_user.id)
    
    return NotificationSettings(
        email_notifications=settings.email_notifications,
        push_notifications=settings.push_notifications,
        bill_reminders=settings.bill_reminders,
        weekly_reports=settings.weekly_reports,
        overdue_invoices=settings.overdue_invoices,
        team_updates=settings.team_updates,
        marketing_emails=settings.marketing_emails,
        expense_summaries=settings.expense_summaries,
        budget_alerts=settings.budget_alerts
    )
