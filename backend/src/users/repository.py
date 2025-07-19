from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func, extract, select
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import uuid

from .models import User, UserRole, UserStatus, UserSettings
from .exceptions import (
    UserNotFoundError, UserValidationError, UserSettingsNotFoundError
)

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # User Repository Methods
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID"""
        result = await self.db.execute(
            select(User).where(User.firebase_uid == firebase_uid)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email_or_firebase_uid(self, email: str, firebase_uid: str) -> Optional[User]:
        """Get user by email or Firebase UID"""
        result = await self.db.execute(
            select(User).where(
                or_(User.email == email, User.firebase_uid == firebase_uid)
            )
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, user: User) -> User:
        """Create new user"""
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            raise UserValidationError(f"Failed to create user: {str(e)}")
    
    async def update_user(self, user: User) -> User:
        """Update user"""
        try:
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            raise UserValidationError(f"Failed to update user: {str(e)}")
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """Get users with filtering and pagination"""
        # Build base query
        query = select(User)
        
        # Apply filters
        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        if search:
            query = query.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return users, total
    
    async def get_user_stats(self) -> dict:
        """Get user statistics for dashboard"""
        # Basic counts
        total_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_result.scalar()
        
        active_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_result.scalar()
        
        verified_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_verified == True)
        )
        verified_users = verified_result.scalar()
        
        # New users this month
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.created_at >= current_month)
        )
        new_users_this_month = new_users_result.scalar()
        
        # Users by role
        role_counts_result = await self.db.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        role_counts = dict(role_counts_result.all())
        users_by_role = {role: role_counts.get(role, 0) for role in UserRole}
        
        # Users by status
        status_counts_result = await self.db.execute(
            select(User.status, func.count(User.id)).group_by(User.status)
        )
        status_counts = dict(status_counts_result.all())
        users_by_status = {status: status_counts.get(status, 0) for status in UserStatus}
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_this_month': new_users_this_month,
            'verified_users': verified_users,
            'users_by_role': users_by_role,
            'users_by_status': users_by_status
        }
    
    # User Settings Repository Methods
    async def get_user_settings(self, user_id: str) -> Optional[UserSettings]:
        """Get user settings by user ID"""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user_settings(self, settings: UserSettings) -> UserSettings:
        """Create new user settings"""
        try:
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
            return settings
        except Exception as e:
            await self.db.rollback()
            raise UserValidationError(f"Failed to create user settings: {str(e)}")
    
    async def update_user_settings(self, settings: UserSettings) -> UserSettings:
        """Update user settings"""
        try:
            settings.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(settings)
            return settings
        except Exception as e:
            await self.db.rollback()
            raise UserValidationError(f"Failed to update user settings: {str(e)}") 