from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import logging

from .models import User, UserRole, UserStatus, UserSettings
from .repository import UserRepository
from .schemas import (
    UserCreate, UserUpdate, UserStatsResponse, UserSettingsUpdate,
    NotificationSettingsUpdate, UserPreferencesUpdate
)
from ..core.database import get_db
from .exceptions import (
    UserNotFoundError, DuplicateEmailError, UserValidationError,
    UserUpdateError, UserSettingsNotFoundError
)

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.user_repo = UserRepository(self.db)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Business logic: Check if user already exists
        existing_user = await self.user_repo.get_user_by_email_or_firebase_uid(
            user_data.email, user_data.firebase_uid
        )
        
        if existing_user:
            raise DuplicateEmailError("User with this email or Firebase UID already exists")
        
        # Business logic: Create new user
        user = User(
            id=str(uuid.uuid4()),
            **user_data.model_dump()
        )
        
        # Delegate to repository for data access
        return await self.user_repo.create_user(user)
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repo.get_user_by_id(user_id)
    
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID"""
        return await self.user_repo.get_user_by_firebase_uid(firebase_uid)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.user_repo.get_user_by_email(email)
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        # Update only provided fields
        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        
        # Delegate to repository for data access
        return await self.user_repo.update_user(user)
    
    async def update_last_login(self, user_id: str) -> User:
        """Update user's last login timestamp"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        user.last_login = datetime.utcnow()
        
        # Delegate to repository for data access
        return await self.user_repo.update_user(user)
    
    async def deactivate_user(self, user_id: str) -> User:
        """Deactivate a user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        user.is_active = False
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.utcnow()
        
        # Delegate to repository for data access
        return await self.user_repo.update_user(user)
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """Get users with filtering and pagination"""
        # Delegate to repository for data access
        return await self.user_repo.get_users(skip, limit, role, status, search)
    
    async def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics for dashboard"""
        # Delegate to repository for data access
        stats_data = await self.user_repo.get_user_stats()
        
        return UserStatsResponse(**stats_data)

    # User Settings Methods

    async def get_user_settings(self, user_id: str) -> UserSettings:
        """Get user settings, create default if doesn't exist"""
        settings = await self.user_repo.get_user_settings(user_id)
        
        if not settings:
            # Create default settings
            settings = await self.create_default_settings(user_id)
        
        return settings

    async def create_default_settings(self, user_id: str) -> UserSettings:
        """Create default settings for a user"""
        settings = UserSettings(
            id=str(uuid.uuid4()),
            user_id=user_id
            # All other fields will use their default values
        )
        
        # Delegate to repository for data access
        return await self.user_repo.create_user_settings(settings)

    async def update_user_settings(self, user_id: str, settings_data: UserSettingsUpdate) -> UserSettings:
        """Update user settings"""
        settings = await self.get_user_settings(user_id)
        
        # Update only provided fields
        for field, value in settings_data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        
        # Delegate to repository for data access
        return await self.user_repo.update_user_settings(settings)

    async def update_notification_settings(self, user_id: str, notification_data: NotificationSettingsUpdate) -> UserSettings:
        """Update only notification settings"""
        settings = await self.get_user_settings(user_id)
        
        # Update only notification fields
        for field, value in notification_data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        
        # Delegate to repository for data access
        return await self.user_repo.update_user_settings(settings)

    async def update_user_preferences(self, user_id: str, preferences_data: UserPreferencesUpdate) -> UserSettings:
        """Update only user preferences (non-notification settings)"""
        settings = await self.get_user_settings(user_id)
        
        # Update only preference fields
        for field, value in preferences_data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        
        # Delegate to repository for data access
        return await self.user_repo.update_user_settings(settings)

    async def reset_settings_to_default(self, user_id: str) -> UserSettings:
        """Reset user settings to default values"""
        settings = await self.get_user_settings(user_id)
        
        # Reset to default values
        default_settings = UserSettings(id="", user_id="")  # Just to get defaults
        for column in UserSettings.__table__.columns:
            if column.name not in ['id', 'user_id', 'created_at', 'updated_at']:
                default_value = column.default.arg if column.default else None
                setattr(settings, column.name, default_value)
        
        # Delegate to repository for data access
        return await self.user_repo.update_user_settings(settings)