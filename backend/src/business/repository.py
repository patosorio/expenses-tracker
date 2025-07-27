from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func
from typing import Optional, List
from uuid import UUID
import logging

from .models import BusinessSettings, TaxConfiguration
from ..core.shared.base_repository import BaseRepository
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class BusinessRepository(BaseRepository[BusinessSettings]):
    """Repository for business settings data access operations extending BaseRepository."""
    
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, BusinessSettings)

    # Business-specific methods only (BaseRepository provides CRUD)
    async def get_by_user_id(self, user_id: str) -> Optional[BusinessSettings]:
        """Get business settings by user ID"""
        try:
            query = select(BusinessSettings).where(BusinessSettings.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error getting business settings by user ID: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving business settings",
                context={"user_id": user_id}
            )
    
    async def exists_for_user(self, user_id: str) -> bool:
        """Check if business settings exist for user"""
        try:
            query = select(func.count(BusinessSettings.id)).where(BusinessSettings.user_id == user_id)
            result = await self.db.execute(query)
            count = result.scalar() or 0
            return count > 0
        except Exception as e:
            logger.error(f"Database error checking business settings existence: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking business settings existence",
                context={"user_id": user_id}
            )


class TaxConfigurationRepository(BaseRepository[TaxConfiguration]):
    """Repository for tax configuration data access operations extending BaseRepository."""
    
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, TaxConfiguration)

    # Tax configuration-specific methods
    async def get_by_name(self, user_id: str, name: str) -> Optional[TaxConfiguration]:
        """Get tax configuration by name for user"""
        try:
            query = select(TaxConfiguration).where(
                and_(
                    TaxConfiguration.user_id == user_id,
                    func.lower(TaxConfiguration.name) == name.lower().strip(),
                    TaxConfiguration.is_active.is_(True)
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error getting tax configuration by name: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving tax configuration by name",
                context={"user_id": user_id, "name": name}
            )

    async def get_default_for_user(self, user_id: str) -> Optional[TaxConfiguration]:
        """Get default tax configuration for user"""
        try:
            query = select(TaxConfiguration).where(
                and_(
                    TaxConfiguration.user_id == user_id,
                    TaxConfiguration.is_default.is_(True),
                    TaxConfiguration.is_active.is_(True)
                )
            )
            result = await self.db.execute(query)
            configs = result.scalars().all()
            
            # Log warning if multiple defaults found
            if len(configs) > 1:
                logger.warning(f"Multiple default tax configurations found for user {user_id}")
            
            return configs[0] if configs else None
        except Exception as e:
            logger.error(f"Database error getting default tax configuration: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving default tax configuration",
                context={"user_id": user_id}
            )

    async def unset_all_defaults(self, user_id: str, exclude_id: str | None = None) -> int:
        """Unset all default tax configurations for user, returns count of updated records"""
        try:
            query = select(TaxConfiguration).where(
                and_(
                    TaxConfiguration.user_id == user_id,
                    TaxConfiguration.is_default.is_(True)
                )
            )
            
            if exclude_id:
                query = query.where(TaxConfiguration.id != exclude_id)
            
            result = await self.db.execute(query)
            configs = result.scalars().all()
            
            updated_count = 0
            for config in configs:
                await self.update(config, {"is_default": False})
                updated_count += 1
            
            logger.info(f"Unset {updated_count} default tax configurations for user {user_id}")
            return updated_count
                
        except Exception as e:
            logger.error(f"Database error unsetting default tax configurations: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while unsetting default tax configurations",
                context={"user_id": user_id, "exclude_id": exclude_id}
            )

    async def check_duplicate_name(
        self, 
        user_id: str, 
        name: str, 
        exclude_id: UUID | None = None
    ) -> bool:
        """Check if tax configuration name already exists for user"""
        try:
            query = select(TaxConfiguration).where(
                and_(
                    TaxConfiguration.user_id == user_id,
                    func.lower(TaxConfiguration.name) == name.lower().strip(),
                    TaxConfiguration.is_active.is_(True)
                )
            )
            
            if exclude_id:
                query = query.where(TaxConfiguration.id != exclude_id)
            
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()
            
            return existing is not None
            
        except Exception as e:
            logger.error(f"Database error checking duplicate tax configuration name: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking duplicate name",
                context={"user_id": user_id, "name": name}
            )

    async def is_tax_config_in_use(self, tax_config_id: UUID) -> bool:
        """Check if tax configuration is currently in use"""
        try:
            # This would check expenses table for usage
            # For now, return False - implement when expenses integration is ready
            return False
        except Exception as e:
            logger.error(f"Database error checking tax configuration usage: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking tax configuration usage",
                context={"tax_config_id": str(tax_config_id)}
            )