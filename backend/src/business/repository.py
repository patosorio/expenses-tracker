from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func
from typing import Optional, List
from uuid import UUID
import logging

from .models import BusinessSettings, TaxConfiguration
from ..core.shared.base_repository import BaseRepository
from .exceptions import (
    TaxConfigurationValidationError, MultipleDefaultTaxConfigsError
)

logger = logging.getLogger(__name__)


class BusinessSettingsRepository(BaseRepository[BusinessSettings]):
    """Repository for business settings data access operations"""
    
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, BusinessSettings)

    # Business settings-specific methods only (BaseRepository provides CRUD)
    async def get_by_user_id(self, user_id: str) -> Optional[BusinessSettings]:
        """Get business settings by user ID"""
        try:
            query = select(BusinessSettings).where(BusinessSettings.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting business settings for user {user_id}: {e!s}")
            raise
    
    async def exists_for_user(self, user_id: str) -> bool:
        """Check if business settings exist for user"""
        try:
            query = select(func.count(BusinessSettings.id)).where(BusinessSettings.user_id == user_id)
            result = await self.db.execute(query)
            count = result.scalar() or 0
            return count > 0
        except Exception as e:
            logger.error(f"Error checking business settings existence for user {user_id}: {e!s}")
            raise


class TaxConfigurationRepository(BaseRepository[TaxConfiguration]):
    """Repository for tax configuration data access operations"""
    
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, TaxConfiguration)

    # Tax configuration-specific methods
    async def get_by_user_id(
        self, 
        user_id: str, 
        active_only: bool = True
    ) -> List[TaxConfiguration]:
        """Get user's tax configurations with filtering"""
        try:
            # Use BaseRepository's get_all with proper filtering
            return await self.get_all(
                user_id=user_id,
                include_inactive=not active_only,
                sort_field="is_default",
                sort_order="desc"
            )
        except Exception as e:
            logger.error(f"Error getting tax configurations for user {user_id}: {e!s}")
            raise

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
            logger.error(f"Error getting tax configuration by name '{name}' for user {user_id}: {e!s}")
            raise

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
            
            # Ensure only one default exists
            if len(configs) > 1:
                logger.warning(f"Multiple default tax configurations found for user {user_id}")
                raise MultipleDefaultTaxConfigsError(
                    detail=f"Found {len(configs)} default tax configurations",
                    context={"user_id": user_id, "count": len(configs)}
                )
            
            return configs[0] if configs else None
        except MultipleDefaultTaxConfigsError:
            raise
        except Exception as e:
            logger.error(f"Error getting default tax configuration for user {user_id}: {e!s}")
            raise

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
            logger.error(f"Error unsetting default tax configurations for user {user_id}: {e!s}")
            raise TaxConfigurationValidationError(
                detail="Failed to unset default tax configurations",
                context={"user_id": user_id, "exclude_id": exclude_id, "original_error": str(e)}
            )

    async def set_as_default(self, tax_config_id: UUID, user_id: str) -> TaxConfiguration:
        """Set a tax configuration as default for user"""
        try:
            # First unset all other defaults
            await self.unset_all_defaults(user_id, exclude_id=str(tax_config_id))
            
            # Get and update the target configuration
            tax_config = await self.get_by_id_or_raise(tax_config_id, user_id)
            return await self.update(tax_config, {"is_default": True})
            
        except Exception as e:
            logger.error(f"Error setting tax configuration {tax_config_id} as default: {e!s}")
            raise TaxConfigurationValidationError(
                detail="Failed to set tax configuration as default",
                context={"tax_config_id": str(tax_config_id), "user_id": user_id, "original_error": str(e)}
            )

    async def count_active_for_user(self, user_id: str) -> int:
        """Count active tax configurations for user"""
        try:
            return await self.count(
                user_id=user_id,
                include_inactive=False
            )
        except Exception as e:
            logger.error(f"Error counting active tax configurations for user {user_id}: {e!s}")
            raise

    async def get_by_tax_rate(
        self, 
        user_id: str, 
        tax_rate: float, 
        tolerance: float = 0.01
    ) -> List[TaxConfiguration]:
        """Get tax configurations by rate with tolerance"""
        try:
            query = select(TaxConfiguration).where(
                and_(
                    TaxConfiguration.user_id == user_id,
                    TaxConfiguration.is_active.is_(True),
                    TaxConfiguration.tax_rate >= (tax_rate - tolerance),
                    TaxConfiguration.tax_rate <= (tax_rate + tolerance)
                )
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting tax configurations by rate {tax_rate} for user {user_id}: {e!s}")
            raise


# Legacy BusinessRepository for backward compatibility (if needed during transition)
class BusinessRepository:
    """Composite repository that provides access to both business settings and tax configurations"""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.business_settings = BusinessSettingsRepository(db)
        self.tax_configurations = TaxConfigurationRepository(db)
    
    # Delegate methods to specific repositories
    async def get_business_settings(self, user_id: str) -> Optional[BusinessSettings]:
        """Get business settings by user ID"""
        return await self.business_settings.get_by_user_id(user_id)
    
    async def create_business_settings(self, settings: BusinessSettings) -> BusinessSettings:
        """Create new business settings"""
        return await self.business_settings.create(settings)
    
    async def update_business_settings(self, settings: BusinessSettings, update_data: dict) -> BusinessSettings:
        """Update business settings"""
        return await self.business_settings.update(settings, update_data)
    
    async def get_tax_configurations(self, user_id: str, active_only: bool = True) -> List[TaxConfiguration]:
        """Get user's tax configurations"""
        return await self.tax_configurations.get_by_user_id(user_id, active_only)
    
    async def get_tax_configuration_by_id(self, tax_id: str, user_id: str) -> Optional[TaxConfiguration]:
        """Get specific tax configuration by ID"""
        return await self.tax_configurations.get_by_id(UUID(tax_id), user_id)
    
    async def create_tax_configuration(self, tax_config: TaxConfiguration) -> TaxConfiguration:
        """Create new tax configuration"""
        return await self.tax_configurations.create(tax_config)
    
    async def update_tax_configuration(self, tax_config: TaxConfiguration, update_data: dict) -> TaxConfiguration:
        """Update tax configuration"""
        return await self.tax_configurations.update(tax_config, update_data)
    
    async def delete_tax_configuration(self, tax_config: TaxConfiguration) -> bool:
        """Soft delete tax configuration"""
        await self.tax_configurations.soft_delete(tax_config)
        return True
    
    async def unset_default_tax_configs(self, user_id: str, exclude_id: str | None = None) -> None:
        """Unset all default tax configurations for user"""
        await self.tax_configurations.unset_all_defaults(user_id, exclude_id)
    
    async def get_default_tax_configuration(self, user_id: str) -> Optional[TaxConfiguration]:
        """Get default tax configuration for user"""
        return await self.tax_configurations.get_default_for_user(user_id)