import re
from typing import List, Dict, Any, Optional
from uuid import UUID
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .models import BusinessSettings, TaxConfiguration
from .repository import BusinessRepository, TaxConfigurationRepository
from .schemas import (
    BusinessSettingsUpdate,
)
from .exceptions import *
from ..core.shared.base_service import BaseService
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)

# Business constants
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "NZD"]
MAX_BUSINESS_NAME_LENGTH = 255
MAX_TAX_CONFIG_NAME_LENGTH = 100
MAX_TAX_CONFIG_DESCRIPTION_LENGTH = 500
MIN_TAX_RATE = 0.0
MAX_TAX_RATE = 100.0
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^\+?[\d\s\-\(\)]{7,20}$')


class BusinessService(BaseService[BusinessSettings, BusinessRepository]):
    """Business service with business logic extending BaseService."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, BusinessRepository, BusinessSettings)

    # Business-specific methods
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
            raise InternalServerError(
                detail="Failed to retrieve business settings",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def create_default_settings(self, user_id: str) -> BusinessSettings:
        """Create default business settings for user"""
        try:
            # Check if settings already exist
            if await self.repository.exists_for_user(user_id):
                raise BusinessSettingsAlreadyExistsError(
                    detail="Business settings already exist for this user",
                    context={"user_id": user_id}
                )
            
            settings_data = {
                "id": str(uuid.uuid4()),
                "business_name": f"Business_{user_id[:8]}",  # Default name
                "currency": "USD",  # Default currency
                "fiscal_year_start": 1,  # January
            }
            
            return await self.create(settings_data, user_id)
        except BusinessSettingsAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Error creating default business settings for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to create default business settings",
                context={"user_id": user_id, "original_error": str(e)}
            )

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
            raise InternalServerError(
                detail="Failed to update business settings",
                context={"user_id": user_id, "original_error": str(e)}
            )

    # Validation hooks
    async def _pre_create_validation(self, entity_data: Dict[str, Any], user_id: str) -> None:
        """Business settings pre-create validation."""
        await self._validate_business_data(entity_data)

    async def _pre_update_validation(self, entity: BusinessSettings, update_data: Dict[str, Any], user_id: str) -> None:
        """Business settings pre-update validation."""
        if not update_data:
            raise BusinessSettingsValidationError(
                detail="No valid fields provided for update",
                context={"settings_id": str(entity.id), "user_id": user_id}
            )
        await self._validate_business_data(update_data)

    async def _validate_business_data(self, data: Dict[str, Any]) -> None:
        """Validate business settings data"""
        # Validate business name
        if "business_name" in data:
            business_name = data["business_name"]
            if not business_name or not business_name.strip():
                raise InvalidBusinessNameError(
                    detail="Business name cannot be empty",
                    context={"business_name": business_name}
                )
            if len(business_name.strip()) > MAX_BUSINESS_NAME_LENGTH:
                raise InvalidBusinessNameError(
                    detail=f"Business name must be {MAX_BUSINESS_NAME_LENGTH} characters or less",
                    context={"business_name": business_name, "length": len(business_name)}
                )
        
        # Validate email format
        if "business_email" in data and data["business_email"]:
            email = data["business_email"].strip()
            if not EMAIL_REGEX.match(email):
                raise InvalidBusinessEmailError(
                    detail="Invalid email format",
                    context={"email": email}
                )
        
        # Validate phone format
        if "business_phone" in data and data["business_phone"]:
            phone = data["business_phone"].strip()
            if not PHONE_REGEX.match(phone):
                raise InvalidBusinessPhoneError(
                    detail="Invalid phone number format",
                    context={"phone": phone}
                )
        
        # Validate currency
        if "currency" in data:
            currency = data["currency"]
            if currency not in SUPPORTED_CURRENCIES:
                raise InvalidCurrencyError(
                    detail=f"Currency must be one of: {', '.join(SUPPORTED_CURRENCIES)}",
                    context={"currency": currency, "supported": SUPPORTED_CURRENCIES}
                )
        
        # Validate tax number format (basic validation)
        if "tax_number" in data and data["tax_number"]:
            tax_number = data["tax_number"].strip()
            if len(tax_number) < 5 or len(tax_number) > 50:
                raise InvalidTaxNumberError(
                    detail="Tax number must be between 5 and 50 characters",
                    context={"tax_number": tax_number}
                )


class TaxConfigurationService(BaseService[TaxConfiguration, TaxConfigurationRepository]):
    """Tax configuration service with business logic extending BaseService."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, TaxConfigurationRepository, TaxConfiguration)

    # Tax configuration-specific methods
    async def get_default_configuration(self, user_id: str) -> Optional[TaxConfiguration]:
        """Get default tax configuration for user"""
        try:
            return await self.repository.get_default_for_user(user_id)
        except Exception as e:
            logger.error(f"Error getting default tax configuration for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Failed to retrieve default tax configuration",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def set_as_default(self, tax_config_id: UUID, user_id: str) -> TaxConfiguration:
        """Set tax configuration as default"""
        try:
            # Get the tax configuration first
            tax_config = await self.get_by_id_or_raise(tax_config_id, user_id)
            
            # Unset all other defaults
            await self.repository.unset_all_defaults(user_id, exclude_id=str(tax_config_id))
            
            # Set this one as default
            return await self.update(tax_config_id, {"is_default": True}, user_id)
            
        except Exception as e:
            logger.error(f"Error setting tax configuration {tax_config_id} as default: {e!s}")
            raise InternalServerError(
                detail="Failed to set tax configuration as default",
                context={"tax_config_id": str(tax_config_id), "user_id": user_id}
            )

    # Validation hooks
    async def _pre_create_validation(self, entity_data: Dict[str, Any], user_id: str) -> None:
        """Tax configuration pre-create validation."""
        await self._validate_tax_configuration_data(entity_data, user_id)
        
        # Check for duplicate name
        if entity_data.get("name"):
            await self._check_duplicate_name(user_id, entity_data["name"])
        
        # Business logic: If setting as default, unset other defaults
        if entity_data.get("is_default"):
            await self.repository.unset_all_defaults(user_id)

    async def _pre_update_validation(self, entity: TaxConfiguration, update_data: Dict[str, Any], user_id: str) -> None:
        """Tax configuration pre-update validation."""
        if not update_data:
            raise TaxConfigurationValidationError(
                detail="No valid fields provided for update",
                context={"tax_config_id": str(entity.id), "user_id": user_id}
            )
            
        await self._validate_tax_configuration_data(update_data, user_id, exclude_id=entity.id)
        
        # Check for duplicate name if name is being updated
        if "name" in update_data and update_data["name"] != entity.name:
            await self._check_duplicate_name(user_id, update_data["name"], exclude_id=entity.id)
        
        # Business logic: If setting as default, unset other defaults
        if update_data.get("is_default"):
            await self.repository.unset_all_defaults(user_id, exclude_id=str(entity.id))

    async def _pre_delete_validation(self, entity: TaxConfiguration, user_id: str) -> None:
        """Tax configuration pre-delete validation."""
        # Check if tax configuration is in use
        if await self.repository.is_tax_config_in_use(entity.id):
            raise TaxConfigurationInUseError(
                detail="Cannot delete tax configuration that is currently in use",
                context={"tax_config_id": str(entity.id)}
            )

    # Private validation methods
    async def _check_duplicate_name(
        self, 
        user_id: str, 
        name: str, 
        exclude_id: UUID | None = None
    ) -> None:
        """Check for duplicate tax configuration name."""
        is_duplicate = await self.repository.check_duplicate_name(user_id, name, exclude_id)
        if is_duplicate:
            raise DuplicateTaxConfigurationError(
                detail=f"Tax configuration '{name}' already exists",
                context={"name": name, "user_id": user_id}
            )

    async def _validate_tax_configuration_data(self, data: Dict[str, Any], user_id: str, exclude_id: UUID | None = None) -> None:
        """Validate tax configuration data"""
        # Validate name
        if "name" in data:
            name = data["name"]
            if not name or not name.strip():
                raise TaxConfigurationValidationError(
                    detail="Tax configuration name cannot be empty",
                    context={"name": name}
                )
            if len(name.strip()) > MAX_TAX_CONFIG_NAME_LENGTH:
                raise TaxConfigurationNameTooLongError(
                    detail=f"Tax configuration name must be {MAX_TAX_CONFIG_NAME_LENGTH} characters or less",
                    context={"name": name, "length": len(name)}
                )
        
        # Validate description
        if "description" in data and data["description"]:
            description = data["description"]
            if len(description.strip()) > MAX_TAX_CONFIG_DESCRIPTION_LENGTH:
                raise TaxConfigurationDescriptionTooLongError(
                    detail=f"Tax configuration description must be {MAX_TAX_CONFIG_DESCRIPTION_LENGTH} characters or less",
                    context={"description": description, "length": len(description)}
                )
        
        # Validate tax rate
        if "tax_rate" in data:
            tax_rate = data["tax_rate"]
            if tax_rate is None:
                raise InvalidTaxRateError(
                    detail="Tax rate cannot be null",
                    context={"tax_rate": tax_rate}
                )
            if not isinstance(tax_rate, (int, float)):
                raise InvalidTaxRateError(
                    detail="Tax rate must be a number",
                    context={"tax_rate": tax_rate, "type": type(tax_rate).__name__}
                )
            if tax_rate < MIN_TAX_RATE or tax_rate > MAX_TAX_RATE:
                raise InvalidTaxRateError(
                    detail=f"Tax rate must be between {MIN_TAX_RATE} and {MAX_TAX_RATE} percent",
                    context={"tax_rate": tax_rate, "min": MIN_TAX_RATE, "max": MAX_TAX_RATE}
                )
            
            # Check decimal precision (max 4 decimal places)
            if isinstance(tax_rate, float):
                decimal_places = len(str(tax_rate).split('.')[-1]) if '.' in str(tax_rate) else 0
                if decimal_places > 4:
                    raise InvalidTaxRateError(
                        detail="Tax rate can have maximum 4 decimal places",
                        context={"tax_rate": tax_rate, "decimal_places": decimal_places}
                    )