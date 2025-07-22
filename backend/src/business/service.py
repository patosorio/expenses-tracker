from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid
from datetime import datetime
import logging

from .models import BusinessSettings, TaxConfiguration
from .repository import BusinessRepository
from .schemas import (
    BusinessSettingsCreate, BusinessSettingsUpdate,
    TaxConfigurationCreate, TaxConfigurationUpdate
)
from .exceptions import (
    BusinessSettingsNotFoundError, TaxConfigurationNotFoundError,
    BusinessValidationError, TaxConfigurationValidationError
)

logger = logging.getLogger(__name__)

class BusinessService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.business_repo = BusinessRepository(db)
    
    # Business Settings Methods
    async def get_business_settings(self, user_id: str) -> BusinessSettings:
        """Get business settings, create default if doesn't exist"""
        settings = await self.business_repo.get_business_settings(user_id)
        
        if not settings:
            settings = await self.create_default_business_settings(user_id)
        
        return settings
    
    async def create_default_business_settings(self, user_id: str) -> BusinessSettings:
        """Create default business settings for user"""
        settings = BusinessSettings(
            id=str(uuid.uuid4()),
            user_id=user_id
        )
        
        # Delegate to repository for data access
        return await self.business_repo.create_business_settings(settings)
    
    async def update_business_settings(
        self, 
        user_id: str, 
        settings_data: BusinessSettingsUpdate
    ) -> BusinessSettings:
        """Update business settings"""
        settings = await self.get_business_settings(user_id)
        
        # Update only provided fields
        for field, value in settings_data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        
        # Delegate to repository for data access
        return await self.business_repo.update_business_settings(settings)
    
    # Tax Configuration Methods
    async def get_tax_configurations(
        self, 
        user_id: str, 
        active_only: bool = True
    ) -> List[TaxConfiguration]:
        """Get user's tax configurations"""
        # Delegate to repository for data access
        return await self.business_repo.get_tax_configurations(user_id, active_only)
    
    async def get_tax_configuration(
        self, 
        tax_id: str, 
        user_id: str
    ) -> TaxConfiguration:
        """Get specific tax configuration"""
        tax_config = await self.business_repo.get_tax_configuration_by_id(tax_id, user_id)
        
        if not tax_config:
            raise TaxConfigurationNotFoundError("Tax configuration not found")
        
        return tax_config
    
    async def create_tax_configuration(
        self, 
        user_id: str, 
        tax_data: TaxConfigurationCreate
    ) -> TaxConfiguration:
        """Create new tax configuration"""
        # Business logic: If setting as default, unset other defaults
        if tax_data.is_default:
            await self.business_repo.unset_default_tax_configs(user_id)
        
        tax_config = TaxConfiguration(
            id=str(uuid.uuid4()),
            user_id=user_id,
            **tax_data.model_dump()
        )
        
        # Delegate to repository for data access
        return await self.business_repo.create_tax_configuration(tax_config)
    
    async def update_tax_configuration(
        self, 
        tax_id: str, 
        user_id: str, 
        tax_data: TaxConfigurationUpdate
    ) -> TaxConfiguration:
        """Update tax configuration"""
        tax_config = await self.get_tax_configuration(tax_id, user_id)
        
        # Business logic: If setting as default, unset other defaults
        if tax_data.is_default:
            await self.business_repo.unset_default_tax_configs(user_id, exclude_id=tax_id)
        
        # Update fields
        for field, value in tax_data.model_dump(exclude_unset=True).items():
            setattr(tax_config, field, value)
        
        # Delegate to repository for data access
        return await self.business_repo.update_tax_configuration(tax_config)
    
    async def delete_tax_configuration(self, tax_id: str, user_id: str) -> bool:
        """Soft delete tax configuration"""
        tax_config = await self.get_tax_configuration(tax_id, user_id)
        
        # Delegate to repository for data access
        return await self.business_repo.delete_tax_configuration(tax_config)
    
    async def _unset_default_tax_configs(self, user_id: str, exclude_id: str = None):
        """Unset all default tax configurations for user"""
        # Delegate to repository for data access
        await self.business_repo.unset_default_tax_configs(user_id, exclude_id) 