from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from typing import Optional, List
import uuid
from datetime import datetime

from .models import BusinessSettings, TaxConfiguration
from .exceptions import (
    BusinessSettingsNotFoundError, TaxConfigurationNotFoundError,
    BusinessValidationError, TaxConfigurationValidationError
)

class BusinessRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Business Settings Repository Methods
    async def get_business_settings(self, user_id: str) -> Optional[BusinessSettings]:
        """Get business settings by user ID"""
        result = await self.db.execute(
            select(BusinessSettings).where(BusinessSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_business_settings(self, settings: BusinessSettings) -> BusinessSettings:
        """Create new business settings"""
        try:
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
            return settings
        except Exception as e:
            await self.db.rollback()
            raise BusinessValidationError(f"Failed to create business settings: {str(e)}")
    
    async def update_business_settings(self, settings: BusinessSettings) -> BusinessSettings:
        """Update business settings"""
        try:
            settings.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(settings)
            return settings
        except Exception as e:
            await self.db.rollback()
            raise BusinessValidationError(f"Failed to update business settings: {str(e)}")
    
    # Tax Configuration Repository Methods
    async def get_tax_configurations(
        self, 
        user_id: str, 
        active_only: bool = True
    ) -> List[TaxConfiguration]:
        """Get user's tax configurations"""
        query = select(TaxConfiguration).where(TaxConfiguration.user_id == user_id)
        
        if active_only:
            query = query.where(TaxConfiguration.is_active == True)
        
        query = query.order_by(TaxConfiguration.is_default.desc(), TaxConfiguration.name)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_tax_configuration_by_id(self, tax_id: str, user_id: str) -> Optional[TaxConfiguration]:
        """Get specific tax configuration by ID"""
        result = await self.db.execute(
            select(TaxConfiguration).where(
                and_(
                    TaxConfiguration.id == tax_id,
                    TaxConfiguration.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_tax_configuration(self, tax_config: TaxConfiguration) -> TaxConfiguration:
        """Create new tax configuration"""
        try:
            self.db.add(tax_config)
            await self.db.commit()
            await self.db.refresh(tax_config)
            return tax_config
        except Exception as e:
            await self.db.rollback()
            raise TaxConfigurationValidationError(f"Failed to create tax configuration: {str(e)}")
    
    async def update_tax_configuration(self, tax_config: TaxConfiguration) -> TaxConfiguration:
        """Update tax configuration"""
        try:
            tax_config.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(tax_config)
            return tax_config
        except Exception as e:
            await self.db.rollback()
            raise TaxConfigurationValidationError(f"Failed to update tax configuration: {str(e)}")
    
    async def delete_tax_configuration(self, tax_config: TaxConfiguration) -> bool:
        """Soft delete tax configuration"""
        try:
            tax_config.is_active = False
            tax_config.updated_at = datetime.utcnow()
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise TaxConfigurationValidationError(f"Failed to delete tax configuration: {str(e)}")
    
    async def unset_default_tax_configs(self, user_id: str, exclude_id: str = None) -> None:
        """Unset all default tax configurations for user"""
        try:
            query = select(TaxConfiguration).where(
                and_(
                    TaxConfiguration.user_id == user_id,
                    TaxConfiguration.is_default == True
                )
            )
            
            if exclude_id:
                query = query.where(TaxConfiguration.id != exclude_id)
            
            result = await self.db.execute(query)
            configs = result.scalars().all()
            
            for config in configs:
                config.is_default = False
            
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise TaxConfigurationValidationError(f"Failed to unset default tax configurations: {str(e)}")
    
    async def get_default_tax_configuration(self, user_id: str) -> Optional[TaxConfiguration]:
        """Get default tax configuration for user"""
        result = await self.db.execute(
            select(TaxConfiguration).where(
                and_(
                    TaxConfiguration.user_id == user_id,
                    TaxConfiguration.is_default == True,
                    TaxConfiguration.is_active == True
                )
            )
        )
        return result.scalar_one_or_none() 