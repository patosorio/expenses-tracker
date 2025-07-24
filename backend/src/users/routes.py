from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from .models import User, UserRole, UserStatus
from .schemas import (
    UserResponse, UserUpdate, UserListResponse, UserStatsResponse,
    UserCreate, UserSettingsResponse, UserSettingsUpdate, UserRegistration
)
from .service import UserService
from ..auth.dependencies import get_current_user, get_admin_user
from ..core.database import get_db
from ..core.shared.decorators import api_endpoint
from ..core.shared.pagination import create_legacy_user_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def register_user(
    registration_data: UserRegistration,
    firebase_uid: str = Query(..., description="Firebase UID from authentication"),
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with Firebase integration."""
    service = UserService(db)
    user = await service.register_user(registration_data, firebase_uid)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    service = UserService(db)
    updated_user = await service.update(
        current_user.id, 
        user_update.model_dump(exclude_unset=True), 
        current_user.id
    )
    return UserResponse.model_validate(updated_user)


@router.get("/", response_model=UserListResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_admin_user),  # Use dependency for admin check
    db: AsyncSession = Depends(get_db)
):
    """Get users with filtering and pagination (Admin only)."""
    service = UserService(db)
    
    filters = {}
    if role:
        filters['role'] = role
    if status:
        filters['status'] = status
    if search:
        filters['search'] = search
    
    users, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    user_responses = [UserResponse.model_validate(user) for user in users]
    return create_legacy_user_response(user_responses, total, skip, limit)


@router.get("/{user_id}", response_model=UserResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID."""
    service = UserService(db)
    
    # Service layer will handle authorization logic
    user = await service.get_user_profile(user_id, current_user.id, current_user.role)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    service = UserService(db)
    
    # Service layer will handle authorization logic
    updated_user = await service.update_user_profile(
        user_id, 
        user_update, 
        current_user.id, 
        current_user.role
    )
    return UserResponse.model_validate(updated_user)


@router.put("/{user_id}/activate", response_model=UserResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_admin_user),  # Admin only dependency
    db: AsyncSession = Depends(get_db)
):
    """Activate user account (Admin only)."""
    service = UserService(db)
    user = await service.activate_user(user_id)
    return UserResponse.model_validate(user)


@router.put("/{user_id}/deactivate", response_model=UserResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_admin_user),  # Admin only dependency
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user account (Admin only)."""
    service = UserService(db)
    user = await service.deactivate_user(user_id, current_user.id)
    return UserResponse.model_validate(user)


@router.get("/stats/overview", response_model=UserStatsResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_user_stats(
    current_user: User = Depends(get_admin_user),  # Admin only dependency
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics (Admin only)."""
    service = UserService(db)
    return await service.get_user_stats()


# User Settings Routes
@router.get("/me/settings", response_model=UserSettingsResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's settings and preferences."""
    service = UserService(db)
    settings = await service.get_user_settings(current_user.id)
    return UserSettingsResponse.model_validate(settings)


@router.put("/me/settings", response_model=UserSettingsResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user settings and preferences."""
    service = UserService(db)
    updated_settings = await service.update_user_settings(current_user.id, settings_data)
    return UserSettingsResponse.model_validate(updated_settings)


@router.post("/me/settings/reset", response_model=UserSettingsResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def reset_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset user settings to default values."""
    service = UserService(db)
    settings = await service.create_default_settings(current_user.id)
    return UserSettingsResponse.model_validate(settings)


# Authentication related endpoints
@router.get("/by-firebase-uid/{firebase_uid}", response_model=UserResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_user_by_firebase_uid(
    firebase_uid: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user by Firebase UID (for authentication)."""
    service = UserService(db)
    user = await service.get_user_by_firebase_uid(firebase_uid)
    if not user:
        from .exceptions import UserNotFoundError
        raise UserNotFoundError(
            detail="User not found",
            context={"firebase_uid": firebase_uid}
        )
    return UserResponse.model_validate(user)


@router.get("/by-email/{email}", response_model=UserResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_user_by_email(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user by email (for authentication)."""
    service = UserService(db)
    user = await service.get_user_by_email(email)
    if not user:
        from .exceptions import UserNotFoundError
        raise UserNotFoundError(
            detail="User not found", 
            context={"email": email}
        )
    return UserResponse.model_validate(user)