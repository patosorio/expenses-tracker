from sqlalchemy.orm import Session
from sqlalchemy import or_, func, extract
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from src.users.models import User, UserRole, UserStatus, UserSettings
from src.users.schemas import (
    UserCreate, UserUpdate, UserStatsResponse, UserSettingsUpdate,
    NotificationSettingsUpdate, UserPreferencesUpdate
)
from src.database import get_db
from src.exceptions import UserNotFoundError, DuplicateEmailError

class UserService:
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            or_(User.email == user_data.email, User.firebase_uid == user_data.firebase_uid)
        ).first()
        
        if existing_user:
            raise DuplicateEmailError("User with this email or Firebase UID already exists")
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            **user_data.model_dump()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID"""
        return self.db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        # Update only provided fields
        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def update_last_login(self, user_id: str) -> User:
        """Update user's last login timestamp"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def deactivate_user(self, user_id: str) -> User:
        """Deactivate a user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        user.is_active = False
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """Get users with filtering and pagination"""
        query = self.db.query(User)
        
        # Apply filters
        if role:
            query = query.filter(User.role == role)
        if status:
            query = query.filter(User.status == status)
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        return users, total
    
    async def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics for dashboard"""
        # Basic counts
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        verified_users = self.db.query(User).filter(User.is_verified == True).count()
        
        # New users this month
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = self.db.query(User).filter(
            User.created_at >= current_month
        ).count()
        
        # Users by role
        role_counts = dict(self.db.query(User.role, func.count(User.id)).group_by(User.role).all())
        users_by_role = {role: role_counts.get(role, 0) for role in UserRole}
        
        # Users by status
        status_counts = dict(self.db.query(User.status, func.count(User.id)).group_by(User.status).all())
        users_by_status = {status: status_counts.get(status, 0) for status in UserStatus}
        
        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            new_users_this_month=new_users_this_month,
            verified_users=verified_users,
            users_by_role=users_by_role,
            users_by_status=users_by_status
        )

    # User Settings Methods

    async def get_user_settings(self, user_id: str) -> UserSettings:
        """Get user settings, create default if doesn't exist"""
        settings = self.db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        
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
        
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        
        return settings

    async def update_user_settings(self, user_id: str, settings_data: UserSettingsUpdate) -> UserSettings:
        """Update user settings"""
        settings = await self.get_user_settings(user_id)
        
        # Update only provided fields
        for field, value in settings_data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(settings)
        
        return settings

    async def update_notification_settings(self, user_id: str, notification_data: NotificationSettingsUpdate) -> UserSettings:
        """Update only notification settings"""
        settings = await self.get_user_settings(user_id)
        
        # Update only notification fields
        for field, value in notification_data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(settings)
        
        return settings

    async def update_user_preferences(self, user_id: str, preferences_data: UserPreferencesUpdate) -> UserSettings:
        """Update only user preferences (non-notification settings)"""
        settings = await self.get_user_settings(user_id)
        
        # Update only preference fields
        for field, value in preferences_data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(settings)
        
        return settings

    async def reset_settings_to_default(self, user_id: str) -> UserSettings:
        """Reset user settings to default values"""
        settings = await self.get_user_settings(user_id)
        
        # Reset to default values
        default_settings = UserSettings(id="", user_id="")  # Just to get defaults
        for column in UserSettings.__table__.columns:
            if column.name not in ['id', 'user_id', 'created_at', 'updated_at']:
                default_value = column.default.arg if column.default else None
                setattr(settings, column.name, default_value)
        
        settings.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(settings)
        
        return settings