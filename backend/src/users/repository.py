from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func, select
from typing import Optional, List, Dict
from datetime import datetime
import logging

from .models import User, UserRole, UserStatus, UserSettings
from ..core.shared.base_repository import BaseRepository
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[User]):
    """Repository for user data access operations extending BaseRepository."""
    def __init__(self, db: AsyncSession) -> None:
        """Initialize UserRepository with database session."""
        super().__init__(db, User)

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID with proper error handling."""
        try:
            result = await self.db.execute(
                select(User).where(User.firebase_uid == firebase_uid)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error retrieving user by Firebase UID: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user by Firebase UID",
                context={"firebase_uid": firebase_uid}
            )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with proper error handling."""
        try:
            result = await self.db.execute(
                select(User).where(func.lower(User.email) == func.lower(email.strip()))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error retrieving user by email: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user by email",
                context={"email": email}
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
        except Exception as e:
            logger.error(f"Database error retrieving user by email or Firebase UID: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user",
                context={"email": email, "firebase_uid": firebase_uid}
            )

    async def get_user_stats(self) -> Dict:
        """Get user statistics for dashboard with optimized queries and error handling."""
        try:
            stats_query = select(
                func.count(User.id).label('total_users'),
                func.count(User.id).filter(User.is_active.is_(True)).label('active_users'),
                func.count(User.id).filter(User.is_verified.is_(True)).label('verified_users'),
                func.count(User.id).filter(
                    User.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                ).label('new_users_this_month')
            )
            result = await self.db.execute(stats_query)
            stats = result.first()
            role_query = select(User.role, func.count(User.id)).group_by(User.role)
            role_result = await self.db.execute(role_query)
            role_counts = dict(role_result.all())
            users_by_role = {role.value: role_counts.get(role, 0) for role in UserRole}
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
        except Exception as e:
            logger.error(f"Database error getting user stats: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user statistics",
                context={"original_error": str(e)}
            )

    async def get_user_settings(self, user_id: str) -> Optional[UserSettings]:
        """Get user settings by user ID with proper error handling."""
        try:
            result = await self.db.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error retrieving user settings for {user_id}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving user settings",
                context={"user_id": user_id}
            )

    async def create_user_settings(self, settings: UserSettings) -> UserSettings:
        """Create new user settings with proper error handling."""
        try:
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
            logger.info(f"User settings created successfully for user: {settings.user_id}")
            return settings
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Database error creating user settings: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while creating user settings",
                context={"user_id": settings.user_id}
            )

    async def update_user_settings(self, settings: UserSettings) -> UserSettings:
        """Update user settings with proper error handling."""
        try:
            settings.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(settings)
            logger.info(f"User settings updated successfully for user: {settings.user_id}")
            return settings
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Database error updating user settings: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while updating user settings",
                context={"user_id": settings.user_id}
            )

    async def is_email_taken(self, email: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if email is already taken by another user."""
        try:
            query = select(User).where(func.lower(User.email) == func.lower(email.strip()))
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Database error checking email availability: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking email availability",
                context={"email": email}
            )

    async def get_users_by_role(self, role: UserRole, include_inactive: bool = False) -> List[User]:
        """Get all users with specific role."""
        try:
            query = select(User).where(User.role == role)
            if not include_inactive:
                query = query.where(User.is_active.is_(True))
            query = query.order_by(User.full_name)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Database error getting users by role {role}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving users by role",
                context={"role": role.value}
            )

    async def count_users_by_status(self, status: UserStatus) -> int:
        """Count users with specific status."""
        try:
            result = await self.db.execute(
                select(func.count(User.id)).where(User.status == status)
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Database error counting users by status {status}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while counting users",
                context={"status": status.value}
            )