"""
Business module for business settings and tax configuration management.

This module provides:
- Business settings model and management
- Tax configuration with multiple tax rates
- Comprehensive business logic for settings operations
- RESTful API endpoints with full CRUD functionality
- Multitenant support with user isolation
"""

from .models import BusinessSettings, TaxConfiguration
from .schemas import (
    BusinessSettingsBase,
    BusinessSettingsCreate,
    BusinessSettingsUpdate,
    BusinessSettingsResponse,
    TaxConfigurationBase,
    TaxConfigurationCreate,
    TaxConfigurationUpdate,
    TaxConfigurationResponse,
    TaxConfigurationListResponse
)
from .service import BusinessService
from .repository import BusinessRepository
from .routes import router
from .exceptions import (
    BusinessSettingsNotFoundError,
    BusinessSettingsValidationError,
    TaxConfigurationNotFoundError,
    TaxConfigurationValidationError,
    TaxConfigurationUpdateError,
    TaxConfigurationDeleteError
)

__all__ = [
    # Models
    "BusinessSettings",
    "TaxConfiguration",
    
    # Schemas
    "BusinessSettingsBase",
    "BusinessSettingsCreate",
    "BusinessSettingsUpdate",
    "BusinessSettingsResponse",
    "TaxConfigurationBase",
    "TaxConfigurationCreate",
    "TaxConfigurationUpdate",
    "TaxConfigurationResponse",
    "TaxConfigurationListResponse",
    
    # Service
    "BusinessService",
    
    # Repository
    "BusinessRepository",
    
    # Router
    "router",
    
    # Exceptions
    "BusinessSettingsNotFoundError",
    "BusinessSettingsValidationError",
    "TaxConfigurationNotFoundError",
    "TaxConfigurationValidationError",
    "TaxConfigurationUpdateError",
    "TaxConfigurationDeleteError"
] 