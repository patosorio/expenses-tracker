from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import uuid
import logging

from .models import BusinessSettings, TaxConfiguration
from .repository import BusinessSettingsRepository, TaxConfigurationRepository, BusinessRepository
from .schemas import (
    BusinessSettingsUpdate,
    TaxConfigurationCreate, TaxConfigurationUpdate
)
from .exceptions import (
    TaxConfigurationNotFoundError,
    BusinessValidationError, TaxConfigurationValidationError
)
from ..core.shared.base_service import BaseService
from ..core.shared.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)


class BusinessSettingsService(BaseService[BusinessSettings, BusinessSettingsRepository]):
    """Service for business settings operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, BusinessSettingsRepository, BusinessSettings)

    async def get_or_create_settings(self, user_id: str) -> BusinessSettings:
        """Get business settings, create default if doesn't exist"""
        try:
            # Try to get existing settings using repository method
            settings = await self.repository.get_by_user_id(user_id)
            
            if not settings:
                settings = await self.create_default_settings(user_id)
            
            return settings
        except Exception as e:
            logger.error(f"Error getting/creating business settings for user {user_id}: {e!s}")
            raise BusinessValidationError(f"Failed to retrieve business settings: {e!s}")

    async def create_default_settings(self, user_id: str) -> BusinessSettings:
        """Create default business settings for user"""
        try:
            settings_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                # Add other default values as needed
            }
            
            return await self.create(settings_data, user_id)
        except Exception as e:
            logger.error(f"Error creating default business settings for user {user_id}: {e!s}")
            raise BusinessValidationError(f"Failed to create default business settings: {e!s}")

    async def update_settings(
        self, 
        user_id: str, 
        settings_data: BusinessSettingsUpdate
    ) -> BusinessSettings:
        """Update business settings"""
        try:
            # Get existing settings (create if not exists)
            settings = await self.get_or_create_settings(user_id)
            
            # Use BaseService update method
            update_dict = settings_data.model_dump(exclude_unset=True)
            return await self.update(UUID(settings.id), update_dict, user_id)
            
        except Exception as e:
            logger.error(f"Error updating business settings for user {user_id}: {e!s}")
            raise BusinessValidationError(f"Failed to update business settings: {e!s}")

    # Validation hooks
    async def _pre_create_validation(self, entity_data: dict, user_id: str) -> None:
        """Validate business settings before creation"""
        # Add business-specific validation here
        pass

    async def _pre_update_validation(self, entity: BusinessSettings, update_data: dict, user_id: str) -> None:
        """Validate business settings before update"""
        # Add business-specific validation here
        pass


class TaxConfigurationService(BaseService[TaxConfiguration, TaxConfigurationRepository]):
    """Service for tax configuration operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, TaxConfigurationRepository, TaxConfiguration)

    async def get_configurations(
        self, 
        user_id: str, 
        active_only: bool = True
    ) -> List[TaxConfiguration]:
        """Get user's tax configurations"""
        try:
            return await self.repository.get_by_user_id(user_id, active_only)
        except Exception as e:
            logger.error(f"Error getting tax configurations for user {user_id}: {e!s}")
            raise TaxConfigurationValidationError(f"Failed to retrieve tax configurations: {e!s}")

    async def get_configuration(self, tax_id: str, user_id: str) -> TaxConfiguration:
        """Get specific tax configuration"""
        try:
            return await self.get_by_id_or_raise(UUID(tax_id), user_id)
        except NotFoundError:
            raise TaxConfigurationNotFoundError("Tax configuration not found")

    async def create_configuration(
        self, 
        user_id: str, 
        tax_data: TaxConfigurationCreate
    ) -> TaxConfiguration:
        """Create new tax configuration"""
        try:
            config_data = {
                "id": str(uuid.uuid4()),
                **tax_data.model_dump()
            }
            
            return await self.create(config_data, user_id)
            
        except Exception as e:
            logger.error(f"Error creating tax configuration for user {user_id}: {e!s}")
            raise TaxConfigurationValidationError(f"Failed to create tax configuration: {e!s}")

    async def update_configuration(
        self, 
        tax_id: str, 
        user_id: str, 
        tax_data: TaxConfigurationUpdate
    ) -> TaxConfiguration:
        """Update tax configuration"""
        try:
            update_dict = tax_data.model_dump(exclude_unset=True)
            return await self.update(UUID(tax_id), update_dict, user_id)
            
        except Exception as e:
            logger.error(f"Error updating tax configuration {tax_id}: {e!s}")
            raise TaxConfigurationValidationError(f"Failed to update tax configuration: {e!s}")

    async def delete_configuration(self, tax_id: str, user_id: str) -> None:
        """Soft delete tax configuration"""
        try:
            await self.delete(UUID(tax_id), user_id, soft=True)
        except Exception as e:
            logger.error(f"Error deleting tax configuration {tax_id}: {e!s}")
            raise TaxConfigurationValidationError(f"Failed to delete tax configuration: {e!s}")

    async def set_as_default(self, tax_id: str, user_id: str) -> TaxConfiguration:
        """Set tax configuration as default"""
        try:
            return await self.repository.set_as_default(UUID(tax_id), user_id)
        except Exception as e:
            logger.error(f"Error setting tax configuration {tax_id} as default: {e!s}")
            raise TaxConfigurationValidationError(f"Failed to set tax configuration as default: {e!s}")

    async def get_default_configuration(self, user_id: str) -> Optional[TaxConfiguration]:
        """Get default tax configuration for user"""
        try:
            return await self.repository.get_default_for_user(user_id)
        except Exception as e:
            logger.error(f"Error getting default tax configuration for user {user_id}: {e!s}")
            raise TaxConfigurationValidationError(f"Failed to retrieve default tax configuration: {e!s}")

    # Validation hooks
    async def _pre_create_validation(self, entity_data: dict, user_id: str) -> None:
        """Validate tax configuration before creation"""
        # Business logic: If setting as default, unset other defaults
        if entity_data.get("is_default"):
            await self.repository.unset_all_defaults(user_id)
        
        # Validate tax rate is reasonable (0-100%)
        if "tax_rate" in entity_data:
            tax_rate = entity_data["tax_rate"]
            if tax_rate < 0 or tax_rate > 100:
                raise ValidationError(
                    detail="Tax rate must be between 0 and 100 percent",
                    context={"tax_rate": tax_rate}
                )

    async def _pre_update_validation(self, entity: TaxConfiguration, update_data: dict, user_id: str) -> None:
        """Validate tax configuration before update"""
        # Business logic: If setting as default, unset other defaults
        if update_data.get("is_default"):
            await self.repository.unset_all_defaults(user_id, exclude_id=str(entity.id))
        
        # Validate tax rate if being updated
        if "tax_rate" in update_data:
            tax_rate = update_data["tax_rate"]
            if tax_rate < 0 or tax_rate > 100:
                raise ValidationError(
                    detail="Tax rate must be between 0 and 100 percent",
                    context={"tax_rate": tax_rate}
                )

    def _get_default_search_fields(self) -> list[str]:
        """Override default search fields for tax configurations"""
        return ["name", "description"]


# Legacy BusinessService for backward compatibility (if needed)
class BusinessService:
    """Composite service that provides access to both business settings and tax configurations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.business_settings_service = BusinessSettingsService(db)
        self.tax_configuration_service = TaxConfigurationService(db)
        
        # For backward compatibility with existing code
        self.business_repo = BusinessRepository(db)

    # Business Settings Methods (delegate to specific service)
    async def get_business_settings(self, user_id: str) -> BusinessSettings:
        """Get business settings, create default if doesn't exist"""
        return await self.business_settings_service.get_or_create_settings(user_id)

    async def create_default_business_settings(self, user_id: str) -> BusinessSettings:
        """Create default business settings for user"""
        return await self.business_settings_service.create_default_settings(user_id)

    async def update_business_settings(
        self, 
        user_id: str, 
        settings_data: BusinessSettingsUpdate
    ) -> BusinessSettings:
        """Update business settings"""
        return await self.business_settings_service.update_settings(user_id, settings_data)

    # Tax Configuration Methods (delegate to specific service)
    async def get_tax_configurations(
        self, 
        user_id: str, 
        active_only: bool = True
    ) -> List[TaxConfiguration]:
        """Get user's tax configurations"""
        return await self.tax_configuration_service.get_configurations(user_id, active_only)

    async def get_tax_configuration(self, tax_id: str, user_id: str) -> TaxConfiguration:
        """Get specific tax configuration"""
        return await self.tax_configuration_service.get_configuration(tax_id, user_id)

    async def create_tax_configuration(
        self, 
        user_id: str, 
        tax_data: TaxConfigurationCreate
    ) -> TaxConfiguration:
        """Create new tax configuration"""
        return await self.tax_configuration_service.create_configuration(user_id, tax_data)

    async def update_tax_configuration(
        self, 
        tax_id: str, 
        user_id: str, 
        tax_data: TaxConfigurationUpdate
    ) -> TaxConfiguration:
        """Update tax configuration"""
        return await self.tax_configuration_service.update_configuration(tax_id, user_id, tax_data)

    async def delete_tax_configuration(self, tax_id: str, user_id: str) -> bool:
        """Soft delete tax configuration"""
        await self.tax_configuration_service.delete_configuration(tax_id, user_id)
        return True

    async def _unset_default_tax_configs(self, user_id: str, exclude_id: str = None):
        """Unset all default tax configurations for user"""
        await self.tax_configuration_service.repository.unset_all_defaults(user_id, exclude_id)