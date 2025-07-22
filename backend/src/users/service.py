from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
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
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidUserDataError,
    AccountDeactivatedError
)
from ..core.shared.exceptions import ValidationError, InternalServerError

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""

        try:
            existing_user = await self.user_repo.get_user_by_email_or_firebase_uid(
                user_data.email, user_data.firebase_uid
            )
            
            if existing_user:
                raise UserAlreadyExistsError(
                        detail=f"User with email {user_data.email} already exists",
                        context={"email": user_data.email, "firebase_uid": user_data.firebase_uid}
                    )
            
            user = User(
                id=str(uuid.uuid4()),
                **user_data.model_dump()
            )
            
            created_user = await self.user_repo.create_user(user)
            logger.info(f"User created successfully: {created_user.id}")
            return created_user
    
        except UserAlreadyExistsError:
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating user: {str(e)}", exc_info=True)
            raise InternalServerError(
                detail="Failed to create user due to internal error",
                context={"original_error": str(e)}
            )
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID - raises exception if not found."""
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(
                    detail=f"User with ID {user_id} not found",
                    context={"user_id": user_id}
                )
            return user
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve user",
                context={"user_id": user_id, "original_error": str(e)}
            )
    
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> User:
        """Get user by Firebase UID - raises exception if not found."""
        try:
            user = await self.user_repo.get_user_by_firebase_uid(firebase_uid)
            if not user:
                raise UserNotFoundError(
                    detail=f"User with Firebase UID not found",
                    context={"firebase_uid": firebase_uid}
                )
            return user
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving user by Firebase UID: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve user by Firebase UID",
                context={"firebase_uid": firebase_uid, "original_error": str(e)}
            )

    async def find_user_by_email(self, email: str) -> Optional[User]:
        """Find user by email - returns None if not found (for optional lookups)."""
        try:
            return await self.user_repo.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            raise InternalServerError(
                detail="Failed to search user by email",
                context={"email": email, "original_error": str(e)}
            )
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user information with validation"""
        try:
            user = await self.get_user_by_id(user_id)
        
            if not user_data.model_dump(exclude_unset=True):
                raise InvalidUserDataError(
                    detail="No valid data provided for update",
                    context={"user_id": user_id}
                )
            # Check for email conflicts
            update_fields = user_data.model_dump(exclude_unset=True)
            if 'email' in update_fields and update_fields['email'] != user.email:
                existing_email_user = await self.find_user_by_email(update_fields['email'])
                if existing_email_user and existing_email_user.id != user_id:
                    raise UserAlreadyExistsError(
                        detail="Email already in use by another user",
                        context={"email": update_fields['email'], "user_id": user_id}
                    )
            # Apply updates
            for field, value in update_fields.items():
                setattr(user, field, value)

            user.updated_at = datetime.utcnow()

            # Delegate to repository for data access
            updated_user = await self.user_repo.update_user(user)
            logger.info(f"User updated successfully: {user_id}")
            return updated_user
        
        except (UserNotFoundError, UserAlreadyExistsError, InvalidUserDataError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to update user",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def update_last_login(self, user_id: str) -> User:
        """Update user's last login timestamp"""
        try:
            user = await self.get_user_by_id(user_id)
            # Check if user is active
            if not user.is_active or user.status == UserStatus.INACTIVE:
                raise AccountDeactivatedError(
                    detail="Cannot update login for deactivated account",
                    context={"user_id": user_id, "status": user.status}
                )
            
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            return await self.user_repo.update_user(user)
        
        except (UserNotFoundError, AccountDeactivatedError):
            raise
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to update last login",
                context={"user_id": user_id, "original_error": str(e)}
            )
    
    async def deactivate_user(self, user_id: str) -> User:
        """Deactivate a user"""
        try:
            user = await self.get_user_by_id(user_id)

            # Check if already deactivated
            if not user.is_active:
                logger.warning(f"Attempting to deactivate already inactive user: {user_id}")
                return user
            
            user.is_active = False
            user.status = UserStatus.INACTIVE
            user.updated_at = datetime.utcnow()
            
            deactivated_user = await self.user_repo.update_user(user)
            logger.info(f"User deactivated successfully: {user_id}")
            return deactivated_user
        
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to deactivate user",
                context={"user_id": user_id, "original_error": str(e)}
            )
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """Get users with filtering and pagination"""
        try:
            # Validate pagination parameters
            if skip < 0:
                raise ValidationError(
                    detail="Skip parameter cannot be negative",
                    context={"skip": skip}
                )
            if limit <= 0 or limit > 1000:
                raise ValidationError(
                    detail="Limit must be between 1 and 1000",
                    context={"limit": limit}
                )
            
            # Delegate to repository
            return await self.user_repo.get_users(skip, limit, role, status, search)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve users",
                context={"original_error": str(e)}
            )
        
    async def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics for dashboard."""
        try:
            stats_data = await self.user_repo.get_user_stats()
            return UserStatsResponse(**stats_data)
        except Exception as e:
            logger.error(f"Error retrieving user stats: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve user statistics",
                context={"original_error": str(e)}
            )


    # User Settings Methods

    async def get_user_settings(self, user_id: str) -> UserSettings:
        """Get user settings, create default if doesn't exist"""
        try:
            # Ensure user exists
            await self.get_user_by_id(user_id)
            
            settings = await self.user_repo.get_user_settings(user_id)
            
            if not settings:
                # Create default settings
                settings = await self.create_default_settings(user_id)
            
            return settings

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving user settings for {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve user settings",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def create_default_settings(self, user_id: str) -> UserSettings:
        """Create default settings for a user"""
        try:
            settings = UserSettings(
                id=str(uuid.uuid4()),
                user_id=user_id
                # All other fields will use their default values
            )

            created_settings = await self.user_repo.create_user_settings(settings)
            logger.info(f"Default settings created for user: {user_id}")
            return created_settings
        
        except Exception as e:
            logger.error(f"Error creating default settings for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to create default user settings",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def update_user_settings(
            self,
            user_id: str,
            settings_data: UserSettingsUpdate
    ) -> UserSettings:
        """Update user settings"""
        try:
            settings = await self.get_user_settings(user_id)

            # Validate that there are fields to update
            update_fields = settings_data.model_dump(exclude_unset=True)
            if not update_fields:
                raise InvalidUserDataError(
                    detail="No valid settings fields provided for update",
                    context={"user_id": user_id}
                )
        
            # Apply updates
            for field, value in update_fields.items():
                setattr(settings, field, value)
            
            settings.updated_at = datetime.utcnow()

            updated_settings = await self.user_repo.update_user_settings(settings)
            logger.info(f"User settings updated for: {user_id}")
            return updated_settings
        
        except (UserNotFoundError, InvalidUserDataError):
            raise
        except Exception as e:
            logger.error(f"Error updating user settings for {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to update user settings",
                context={"user_id": user_id, "original_error": str(e)}
            )
    
    async def update_notification_preferences(
            self,
            user_id: str,
            notification_data: NotificationSettingsUpdate
    ) -> UserSettings:
        """Update notification settings with specialized validation."""

        try:
            settings = await self.get_user_settings(user_id)

            # Validate notification-specific fields
            update_fields = notification_data.model_dump(exclude_unset=True)
            if not update_fields:
                raise InvalidUserDataError(
                    detail="No valid notification fields provided for update",
                    context={"user_id": user_id}
                )
            
            # Business logic: Validate notification preferences
            if 'email_notifications' in update_fields and update_fields['email_notifications']:
                # Ensure user has verified email for notifications
                user = await self.get_user_by_id(user_id)
                if not user.email_verified:
                    raise InvalidUserDataError(
                        detail="Email must be verified to enable email notifications",
                        context={"user_id": user_id, "email_verified": user.email_verified}
                    )
            
            # Apply updates
            for field, value in update_fields.items():
                setattr(settings, field, value)

            settings.updated_at = datetime.utcnow()

            updated_settings = await self.user_repo.update_user_settings(settings)
            logger.info(f"User settings updated for: {user_id}")
            return updated_settings
        
        except (UserNotFoundError, InvalidUserDataError):
            raise
        except Exception as e:
            logger.error(f"Error updating notification settings for {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to update notification settings",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def update_display_preferences(
            self,
            user_id: str,
            preferences_data: UserPreferencesUpdate
    ) -> UserSettings:
        """Update display/UI preferences with specialized validation."""
        try:
            settings = await self.get_user_settings(user_id)
            
            # Validate preference fields
            update_fields = preferences_data.model_dump(exclude_unset=True)
            if not update_fields:
                raise InvalidUserDataError(
                    detail="No valid preference fields provided for update",
                    context={"user_id": user_id}
                )
            
             # Business logic: Validate specific preferences
            if 'currency' in update_fields:
                # Validate currency code
                currency = update_fields['currency']
                if len(currency) != 3 or not currency.isupper():
                    raise InvalidUserDataError(
                        detail="Currency must be a valid 3-letter ISO code",
                        context={"user_id": user_id, "currency": currency}
                    )
            
            if 'timezone' in update_fields:
                timezone = update_fields['timezone']
                if not timezone or len(timezone) > 50:
                    raise InvalidUserDataError(
                        detail="Invalid timezone format",
                        context={"user_id": user_id, "timezone": timezone}
                    )
            
            # Apply updates
            for field, value in update_fields.items():
                setattr(settings, field, value)

            settings.updated_at = datetime.utcnow()

            updated_settings = await self.user_repo.update_user_settings(settings)
            logger.info(f"Display preferences updated for user: {user_id}")
            return updated_settings
        
        except (UserNotFoundError, InvalidUserDataError):
            raise
        except Exception as e:
            logger.error(f"Error updating display preferences for {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to update display preferences",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def reset_settings_to_default(self, user_id: str) -> UserSettings:
        """Reset user settings to default values with proper error handling."""
        try:
            settings = await self.get_user_settings(user_id)
            
            # Reset to default values (preserve id, user_id, timestamps)
            default_settings = UserSettings(id="", user_id="")
            for column in UserSettings.__table__.columns:
                if column.name not in ['id', 'user_id', 'created_at', 'updated_at']:
                    default_value = column.default.arg if column.default else None
                    setattr(settings, column.name, default_value)
            
            settings.updated_at = datetime.utcnow()
            
            reset_settings = await self.user_repo.update_user_settings(settings)
            logger.info(f"User settings reset to default for: {user_id}")
            return reset_settings 
        
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error resetting user settings for {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to reset user settings",
                context={"user_id": user_id, "original_error": str(e)}
            )
