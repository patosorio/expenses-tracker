from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
import uuid
from datetime import datetime

from src.business.models import BusinessSettings, TaxConfiguration
from src.business.schemas import (
    BusinessSettingsCreate, BusinessSettingsUpdate,
    TaxConfigurationCreate, TaxConfigurationUpdate
)
from src.exceptions import BusinessSettingsNotFoundError, TaxConfigurationNotFoundError

class BusinessService:
    def __init__(self, db: Session):
        self.db = db
    
    # Business Settings Methods
    async def get_business_settings(self, user_id: str) -> BusinessSettings:
        """Get business settings, create default if doesn't exist"""
        settings = self.db.query(BusinessSettings).filter(
            BusinessSettings.user_id == user_id
        ).first()
        
        if not settings:
            settings = await self.create_default_business_settings(user_id)
        
        return settings
    
    async def create_default_business_settings(self, user_id: str) -> BusinessSettings:
        """Create default business settings for user"""
        settings = BusinessSettings(
            id=str(uuid.uuid4()),
            user_id=user_id
        )
        
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        
        return settings
    
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
        
        settings.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(settings)
        
        return settings
    
    # Tax Configuration Methods
    async def get_tax_configurations(
        self, 
        user_id: str, 
        active_only: bool = True
    ) -> List[TaxConfiguration]:
        """Get user's tax configurations"""
        query = self.db.query(TaxConfiguration).filter(
            TaxConfiguration.user_id == user_id
        )
        
        if active_only:
            query = query.filter(TaxConfiguration.is_active == True)
        
        return query.order_by(TaxConfiguration.is_default.desc(), TaxConfiguration.name).all()
    
    async def get_tax_configuration(
        self, 
        tax_id: str, 
        user_id: str
    ) -> TaxConfiguration:
        """Get specific tax configuration"""
        tax_config = self.db.query(TaxConfiguration).filter(
            and_(
                TaxConfiguration.id == tax_id,
                TaxConfiguration.user_id == user_id
            )
        ).first()
        
        if not tax_config:
            raise TaxConfigurationNotFoundError("Tax configuration not found")
        
        return tax_config
    
    async def create_tax_configuration(
        self, 
        user_id: str, 
        tax_data: TaxConfigurationCreate
    ) -> TaxConfiguration:
        """Create new tax configuration"""
        # If setting as default, unset other defaults
        if tax_data.is_default:
            await self._unset_default_tax_configs(user_id)
        
        tax_config = TaxConfiguration(
            id=str(uuid.uuid4()),
            user_id=user_id,
            **tax_data.model_dump()
        )
        
        self.db.add(tax_config)
        self.db.commit()
        self.db.refresh(tax_config)
        
        return tax_config
    
    async def update_tax_configuration(
        self, 
        tax_id: str, 
        user_id: str, 
        tax_data: TaxConfigurationUpdate
    ) -> TaxConfiguration:
        """Update tax configuration"""
        tax_config = await self.get_tax_configuration(tax_id, user_id)
        
        # If setting as default, unset other defaults
        if tax_data.is_default:
            await self._unset_default_tax_configs(user_id, exclude_id=tax_id)
        
        # Update fields
        for field, value in tax_data.model_dump(exclude_unset=True).items():
            setattr(tax_config, field, value)
        
        tax_config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(tax_config)
        
        return tax_config
    
    async def delete_tax_configuration(self, tax_id: str, user_id: str) -> bool:
        """Soft delete tax configuration"""
        tax_config = await self.get_tax_configuration(tax_id, user_id)
        
        tax_config.is_active = False
        tax_config.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    async def _unset_default_tax_configs(self, user_id: str, exclude_id: str = None):
        """Unset all default tax configurations for user"""
        query = self.db.query(TaxConfiguration).filter(
            and_(
                TaxConfiguration.user_id == user_id,
                TaxConfiguration.is_default == True
            )
        )
        
        if exclude_id:
            query = query.filter(TaxConfiguration.id != exclude_id)
        
        for config in query.all():
            config.is_default = False
        
        self.db.commit() 