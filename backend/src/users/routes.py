from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import math

from src.users.models import User, UserRole, UserStatus
from src.users.schemas import (
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
from src.users.service import UserService
from src.auth.dependencies import get_current_user
from src.database import get_db
from src.exceptions import DuplicateEmailError

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    try:
        user_service = UserService(db)
        user = await user_service.create_user(user_data)
        return user
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error creating user: {str(e)}")  # For debugging
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )

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
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(current_user.id, user_update)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get users with filtering and pagination (Admin only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
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
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=math.ceil(total / limit)
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (Admin/Manager only or own profile)"""
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (Admin only or own profile)"""
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(user_id, user_update)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate user (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        user_service = UserService(db)
        await user_service.deactivate_user(user_id)
        return {"message": "User deactivated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics (Admin/Manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_service = UserService(db)
    return await user_service.get_user_stats()


# User Settings Routes

@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's settings and preferences"""
    try:
        user_service = UserService(db)
        settings = await user_service.get_user_settings(current_user.id)
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user settings: {str(e)}"
        )

@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings and preferences"""
    try:
        user_service = UserService(db)
        updated_settings = await user_service.update_user_settings(current_user.id, settings_data)
        return updated_settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}"
        )

@router.put("/me/notifications", response_model=UserSettingsResponse)
async def update_notification_settings(
    notification_data: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences only"""
    try:
        user_service = UserService(db)
        updated_settings = await user_service.update_notification_settings(current_user.id, notification_data)
        return updated_settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification settings: {str(e)}"
        )

@router.put("/me/preferences", response_model=UserSettingsResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences only (non-notification settings)"""
    try:
        user_service = UserService(db)
        updated_settings = await user_service.update_user_preferences(current_user.id, preferences_data)
        return updated_settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )

@router.post("/me/settings/reset", response_model=UserSettingsResponse)
async def reset_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset user settings to default values"""
    try:
        user_service = UserService(db)
        reset_settings = await user_service.reset_settings_to_default(current_user.id)
        return reset_settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset user settings: {str(e)}"
        )

@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get only user preferences (for quick access)"""
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user preferences: {str(e)}"
        )

@router.get("/me/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get only notification settings (for quick access)"""
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification settings: {str(e)}"
        )