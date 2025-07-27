from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import re

from .models import User, UserRole, UserStatus, UserSettings
from .repository import UserRepository
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserStatsResponse, 
    UserSettingsUpdate, UserListResponse, UserSettingsResponse
)

from .exceptions import *
from ..core.shared.base_service import BaseService
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class UserService(BaseService[User, UserRepository]):
    """User service with business logic extending BaseService."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, UserRepository, User)

    # User-specific business methods (NOT generic CRUD)
    async def register_user(
        self, 
        registration_data: UserCreate, 
        firebase_uid: str
    ) -> User:
        """Register a new user with Firebase integration."""
        try:
            data = registration_data.model_dump()
            data['firebase_uid'] = firebase_uid
            data['role'] = UserRole.USER  # Default role
            data['status'] = UserStatus.ACTIVE
            data['is_verified'] = False  # Email verification pending
            
            # Use BaseService.create() with validation hooks
            user = await self.create(data, data['id'])  # Use email as temp user_id for validation
            
            # Create default settings
            await self.create_default_settings(user.id)
            
            return user
            
        except (UserAlreadyExistsError, DuplicateEmailError, InvalidEmailError):
            raise
        except Exception as e:
            logger.error(f"Error registering user: {e!s}")
            raise InternalServerError(
                detail="Failed to register user",
                context={"email": registration_data.email, "original_error": str(e)}
            )

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID for authentication."""
        try:
            return await self.repository.get_user_by_firebase_uid(firebase_uid)
        except Exception as e:
            logger.error(f"Error getting user by Firebase UID: {e!s}")
            raise InternalServerError(
                detail="Failed to retrieve user by Firebase UID",
                context={"firebase_uid": firebase_uid}
            )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email for authentication."""
        try:
            return await self.repository.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email: {e!s}")
            raise InternalServerError(
                detail="Failed to retrieve user by email",
                context={"email": email}
            )

    async def update_last_login(self, user_id: str) -> User:
        """Update user's last login timestamp."""
        try:
            update_data = {
                'last_login': datetime.utcnow()
            }
            return await self.update(user_id, update_data, user_id)
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to update last login",
                context={"user_id": user_id}
            )

    async def activate_user(self, user_id: str) -> User:
        """Activate a user account."""
        try:
            user = await self.get_by_id_or_raise(user_id, user_id)
            
            if user.status == UserStatus.ACTIVE:
                raise InvalidUserDataError(
                    detail="User is already active",
                    context={"user_id": user_id}
                )
            
            update_data = {
                'status': UserStatus.ACTIVE,
                'is_verified': True
            }
            
            return await self.update(user_id, update_data, user_id)
            
        except (UserNotFoundError, InvalidUserDataError):
            raise
        except Exception as e:
            logger.error(f"Error activating user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to activate user",
                context={"user_id": user_id}
            )

    async def deactivate_user(self, user_id: str, admin_user_id: str) -> User:
        """Deactivate a user account (admin only)."""
        try:
            user = await self.get_by_id_or_raise(user_id, admin_user_id)
            
            if user.status == UserStatus.SUSPENDED:
                raise InvalidUserDataError(
                    detail="User is already deactivated",
                    context={"user_id": user_id}
                )
            
            update_data = {'status': UserStatus.SUSPENDED}
            return await self.update(user_id, update_data, admin_user_id)
            
        except (UserNotFoundError, InvalidUserDataError):
            raise
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to deactivate user",
                context={"user_id": user_id, "admin_user_id": admin_user_id}
            )

    async def update_user_profile(self, user_id: str, profile_data: UserResponse) -> User:
        """Update user profile information."""
        try:
            update_data = profile_data.model_dump(exclude_unset=True)
            return await self.update(user_id, update_data, user_id)
            
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to update user profile",
                context={"user_id": user_id}
            )

    async def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics for admin dashboard."""
        try:
            stats_data = await self.repository.get_user_stats()
            return UserStatsResponse(**stats_data)
        except Exception as e:
            logger.error(f"Error retrieving user stats: {e!s}")
            raise InternalServerError(
                detail="Failed to retrieve user statistics",
                context={"original_error": str(e)}
            )

    # User Settings Management
    async def get_user_settings(self, user_id: str) -> UserSettings:
        """Get user settings, create default if doesn't exist."""
        try:
            settings = await self.repository.get_user_settings(user_id)
            if not settings:
                settings = await self.create_default_settings(user_id)
            return settings
        except Exception as e:
            logger.error(f"Error retrieving user settings for {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to retrieve user settings",
                context={"user_id": user_id}
            )

    async def create_default_settings(self, user_id: str) -> UserSettings:
        """Create default settings for a user."""
        try:
            settings = UserSettings(
                id=str(uuid.uuid4()),
                user_id=user_id,
                # Add default values
                theme='light',
                language='en',
                timezone='UTC',
                currency='USD',
                notifications_enabled=True,
                email_notifications=True
            )
            created_settings = await self.repository.create_user_settings(settings)
            logger.info(f"Default settings created for user: {user_id}")
            return created_settings
        except Exception as e:
            logger.error(f"Error creating default settings for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to create default user settings",
                context={"user_id": user_id}
            )

    async def update_user_settings(
        self, 
        user_id: str, 
        settings_data: UserSettingsUpdate
    ) -> UserSettings:
        """Update user settings."""
        try:
            settings = await self.get_user_settings(user_id)
            update_fields = settings_data.model_dump(exclude_unset=True)
            
            if not update_fields:
                raise InvalidUserDataError(
                    detail="No valid settings fields provided for update",
                    context={"user_id": user_id}
                )
            
            for field, value in update_fields.items():
                setattr(settings, field, value)
            
            settings.updated_at = datetime.utcnow()
            updated_settings = await self.repository.update_user_settings(settings)
            logger.info(f"User settings updated for: {user_id}")
            return updated_settings
            
        except (UserNotFoundError, InvalidUserDataError):
            raise
        except Exception as e:
            logger.error(f"Error updating user settings for {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to update user settings",
                context={"user_id": user_id}
            )

    # Override BaseService validation hooks with REAL validation
    async def _pre_create_validation(self, entity_data: Dict[str, Any], user_id: str) -> None:
        """User-specific pre-create validation."""
        await self._validate_user_data(entity_data)
        
        # Check for duplicate email
        if entity_data.get('email'):
            await self._check_duplicate_email(entity_data['email'])
        
        # Validate Firebase UID uniqueness
        if entity_data.get('firebase_uid'):
            await self._check_duplicate_firebase_uid(entity_data['firebase_uid'])

    async def _pre_update_validation(
        self, 
        entity: User, 
        update_data: Dict[str, Any], 
        user_id: str
    ) -> None:
        """User-specific pre-update validation."""
        if update_data:
            await self._validate_user_data(update_data, is_update=True)
        
        # Check email uniqueness if changing email
        if 'email' in update_data and update_data['email'] != entity.email:
            await self._check_duplicate_email(update_data['email'], exclude_user_id=entity.id)

    async def _pre_delete_validation(self, entity: User, user_id: str) -> None:
        """User-specific pre-delete validation."""
        # Check if user can be deleted (e.g., has no active data)
        # For now, only allow deactivation, not deletion
        raise InvalidUserDataError(
            detail="Users cannot be deleted, only deactivated",
            context={"user_id": entity.id}
        )

    # Private validation methods
    async def _validate_user_data(self, data: Dict[str, Any], is_update: bool = False) -> None:
        """Validate user data."""
        if not is_update:
            self._validate_required_fields(data, ['email', 'full_name'])
        
        # Validate email format
        if 'email' in data and data['email']:
            self._validate_email_format(data['email'])
        
        # Validate full name
        if 'full_name' in data and data['full_name']:
            if len(data['full_name'].strip()) < 2:
                raise InvalidUserDataError(
                    detail="Full name must be at least 2 characters",
                    context={"full_name": data['full_name']}
                )

    def _validate_email_format(self, email: str) -> None:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            raise InvalidEmailError(
                detail="Invalid email format",
                context={"email": email}
            )

    async def _check_duplicate_email(self, email: str, exclude_user_id: Optional[str] = None) -> None:
        """Check for duplicate email addresses."""
        is_taken = await self.repository.is_email_taken(email, exclude_user_id)
        if is_taken:
            raise DuplicateEmailError(
                detail=f"Email '{email}' is already registered",
                context={"email": email}
            )

    async def _check_duplicate_firebase_uid(self, firebase_uid: str) -> None:
        """Check for duplicate Firebase UIDs."""
        existing_user = await self.repository.get_user_by_firebase_uid(firebase_uid)
        if existing_user:
            raise UserAlreadyExistsError(
                detail="Firebase UID already registered",
                context={"firebase_uid": firebase_uid}
            )