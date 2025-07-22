from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func, extract, select, and_
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import uuid
import logging

from ..users.models import User, UserRole, UserStatus, UserSettings
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data access operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # User Repository Methods
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID with proper error handling."""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user",
                context={"user_id": user_id, "original_error": str(e)}
            )
    
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID with proper error handling."""
        try:
            result = await self.db.execute(
                select(User).where(User.firebase_uid == firebase_uid)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user by Firebase UID: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user by Firebase UID",
                context={"firebase_uid": firebase_uid, "original_error": str(e)}
            )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with proper error handling."""
        try:
            result = await self.db.execute(
                select(User).where(func.lower(User.email) == func.lower(email.strip()))
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user by email: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user by email",
                context={"email": email, "original_error": str(e)}
            )
    
    async def get_user_by_email_or_firebase_uid(self, email: str, firebase_uid: str) -> Optional[User]:
        """Get user by email or Firebase UID with proper error handling."""
        try:
            result = await self.db.execute(
                select(User).where(
                    or_(
                        func.lower(User.email) == func.lower(email.strip()),
                        User.firebase_uid == firebase_uid
                    )
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user by email or Firebase UID: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user",
                context={"email": email, "firebase_uid": firebase_uid, "original_error": str(e)}
            )
    
    async def create_user(self, user: User) -> User:
        """Create new user with proper error handling and transaction management."""
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"User created successfully: {user.id}")
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating user: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while creating user",
                context={"user_email": user.email, "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating user: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while creating user",
                context={"user_email": user.email, "original_error": str(e)}
            )
    
    async def update_user(self, user: User) -> User:
        """Update user with proper error handling and transaction management."""
        try:
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"User updated successfully: {user.id}")
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating user {user.id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while updating user",
                context={"user_id": user.id, "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error updating user {user.id}: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while updating user",
                context={"user_id": user.id, "original_error": str(e)}
            )
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """Get users with filtering and pagination - optimized with proper error handling."""
        try:
            # Build base query
            query = select(User)
            
            # Apply filters
            conditions = []
            
            if role:
                conditions.append(User.role == role)
            if status:
                conditions.append(User.status == status)
            if search:
                search_term = f"%{search.strip()}%"
                search_condition = or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
                conditions.append(search_condition)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count efficiently
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination and ordering
            query = (query
                    .order_by(User.created_at.desc())
                    .offset(skip)
                    .limit(limit))
                    
            result = await self.db.execute(query)
            users = list(result.scalars().all())
            
            return users, total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting users: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving users",
                context={"skip": skip, "limit": limit, "original_error": str(e)}
            )
    
    async def get_user_stats(self) -> dict:
        """Get user statistics for dashboard with optimized queries and error handling."""
        try:
            # Use a single query with conditional aggregates for better performance
            stats_query = select(
                func.count(User.id).label('total_users'),
                func.count(User.id).filter(User.is_active == True).label('active_users'),
                func.count(User.id).filter(User.is_verified == True).label('verified_users'),
                func.count(User.id).filter(
                    User.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                ).label('new_users_this_month')
            )
            
            result = await self.db.execute(stats_query)
            stats = result.first()
            
            # Get role distribution
            role_query = select(User.role, func.count(User.id)).group_by(User.role)
            role_result = await self.db.execute(role_query)
            role_counts = dict(role_result.all())
            users_by_role = {role.value: role_counts.get(role, 0) for role in UserRole}
            
            # Get status distribution
            status_query = select(User.status, func.count(User.id)).group_by(User.status)
            status_result = await self.db.execute(status_query)
            status_counts = dict(status_result.all())
            users_by_status = {status.value: status_counts.get(status, 0) for status in UserStatus}
            
            return {
                'total_users': stats.total_users or 0,
                'active_users': stats.active_users or 0,
                'new_users_this_month': stats.new_users_this_month or 0,
                'verified_users': stats.verified_users or 0,
                'users_by_role': users_by_role,
                'users_by_status': users_by_status
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user stats: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user statistics",
                context={"original_error": str(e)}
            )
    
    # User Settings Repository Methods
    async def get_user_settings(self, user_id: str) -> Optional[UserSettings]:
        """Get user settings by user ID with proper error handling."""
        try:
            result = await self.db.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user settings for {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user settings",
                context={"user_id": user_id, "original_error": str(e)}
            )
    
    async def create_user_settings(self, settings: UserSettings) -> UserSettings:
        """Create new user settings with proper error handling."""
        try:
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
            logger.info(f"User settings created successfully for user: {settings.user_id}")
            return settings
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating user settings: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while creating user settings",
                context={"user_id": settings.user_id, "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating user settings: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while creating user settings",
                context={"user_id": settings.user_id, "original_error": str(e)}
            )
    
    async def update_user_settings(self, settings: UserSettings) -> UserSettings:
        """Update user settings with proper error handling."""
        try:
            settings.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(settings)
            logger.info(f"User settings updated successfully for user: {settings.user_id}")
            return settings
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating user settings: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while updating user settings",
                context={"user_id": settings.user_id, "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error updating user settings: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while updating user settings",
                context={"user_id": settings.user_id, "original_error": str(e)}
            )
    
    # Additional helper methods for business logic support
    async def is_email_taken(self, email: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if email is already taken by another user."""
        try:
            query = select(User).where(func.lower(User.email) == func.lower(email.strip()))
            
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking email availability: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking email availability",
                context={"email": email, "original_error": str(e)}
            )
    
    async def get_users_by_role(self, role: UserRole, include_inactive: bool = False) -> List[User]:
        """Get all users with specific role."""
        try:
            query = select(User).where(User.role == role)
            
            if not include_inactive:
                query = query.where(User.is_active == True)
                
            query = query.order_by(User.full_name)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting users by role {role}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving users by role",
                context={"role": role.value, "original_error": str(e)}
            )
    
    async def count_users_by_status(self, status: UserStatus) -> int:
        """Count users with specific status."""
        try:
            result = await self.db.execute(
                select(func.count(User.id)).where(User.status == status)
            )
            return result.scalar() or 0
            
        except SQLAlchemyError as e:
            logger.error(f"Database error counting users by status {status}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while counting users",
                context={"status": status.value, "original_error": str(e)}
            )