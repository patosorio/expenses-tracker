from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging

from .service import BusinessService, TaxConfigurationService
from .schemas import (
    BusinessSettingsResponse, BusinessSettingsUpdate, BusinessSettingsCreate,
    TaxConfigurationResponse, TaxConfigurationCreate, TaxConfigurationUpdate,
    TaxConfigurationListResponse, BusinessStatsResponse
)
from ..auth.dependencies import get_current_user
from ..users.models import User
from ..core.database import get_db
from ..core.shared.decorators import api_endpoint
from ..core.shared.pagination import create_legacy_tax_configuration_response

router = APIRouter()
logger = logging.getLogger(__name__)


# Business Settings Routes
@router.get("/settings", response_model=BusinessSettingsResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_business_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get business settings for current user."""
    service = BusinessService(db)
    settings = await service.get_or_create_settings(current_user.id)
    return BusinessSettingsResponse.model_validate(settings)


@router.put("/settings", response_model=BusinessSettingsResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_business_settings(
    settings_data: BusinessSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update business settings."""
    service = BusinessService(db)
    settings = await service.update_settings(current_user.id, settings_data)
    return BusinessSettingsResponse.model_validate(settings)


@router.post("/settings", response_model=BusinessSettingsResponse, status_code=status.HTTP_201_CREATED)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def create_business_settings(
    settings_data: BusinessSettingsCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create business settings (explicit creation)."""
    service = BusinessService(db)
    create_data = settings_data.model_dump()
    settings = await service.create(create_data, current_user.id)
    return BusinessSettingsResponse.model_validate(settings)


# Tax Configuration Routes
@router.get("/tax-configurations", response_model=TaxConfigurationListResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_tax_configurations(
    active_only: bool = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tax configurations with filtering and pagination."""
    service = TaxConfigurationService(db)
    filters = {"is_active": True} if active_only else {}
    configurations, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters=filters,
        sort_field="is_default",
        sort_order="desc"
    )
    return create_legacy_tax_configuration_response(configurations, total, skip, limit)


@router.post("/tax-configurations", response_model=TaxConfigurationResponse, status_code=status.HTTP_201_CREATED)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def create_tax_configuration(
    tax_data: TaxConfigurationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new tax configuration."""
    service = TaxConfigurationService(db)
    create_data = tax_data.model_dump()
    tax_config = await service.create(create_data, current_user.id)
    return TaxConfigurationResponse.model_validate(tax_config)


@router.get("/tax-configurations/{tax_id}", response_model=TaxConfigurationResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_tax_configuration(
    tax_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific tax configuration."""
    service = TaxConfigurationService(db)
    tax_config = await service.get_by_id_or_raise(tax_id, current_user.id)
    return TaxConfigurationResponse.model_validate(tax_config)


@router.put("/tax-configurations/{tax_id}", response_model=TaxConfigurationResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_tax_configuration(
    tax_id: UUID,
    tax_data: TaxConfigurationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update tax configuration."""
    service = TaxConfigurationService(db)
    update_data = tax_data.model_dump(exclude_unset=True)
    tax_config = await service.update(tax_id, update_data, current_user.id)
    return TaxConfigurationResponse.model_validate(tax_config)


@router.delete("/tax-configurations/{tax_id}", status_code=status.HTTP_204_NO_CONTENT)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def delete_tax_configuration(
    tax_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete tax configuration."""
    service = TaxConfigurationService(db)
    await service.delete(tax_id, current_user.id, soft=True)
    # No return needed for 204 status


@router.post("/tax-configurations/{tax_id}/set-default", response_model=TaxConfigurationResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def set_default_tax_configuration(
    tax_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set tax configuration as default."""
    service = TaxConfigurationService(db)
    tax_config = await service.set_as_default(tax_id, current_user.id)
    return TaxConfigurationResponse.model_validate(tax_config)


@router.get("/tax-configurations/default/current", response_model=TaxConfigurationResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_default_tax_configuration(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current default tax configuration."""
    service = TaxConfigurationService(db)
    tax_config = await service.get_default_configuration(current_user.id)
    if not tax_config:
        return None
    return TaxConfigurationResponse.model_validate(tax_config)


# Statistics and Summary Routes
@router.get("/stats", response_model=BusinessStatsResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_business_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get business statistics overview."""
    # Use both services to gather comprehensive stats
    business_service = BusinessService(db)
    tax_service = TaxConfigurationService(db)
    
    # Get tax configuration count
    total_tax_configs = await tax_service.count(current_user.id, include_inactive=False)
    active_tax_configs = await tax_service.count(current_user.id, include_inactive=False)
    
    # Get default tax configuration
    default_tax_config = await tax_service.get_default_configuration(current_user.id)
    
    # Check if business settings exist
    settings_exist = await business_service.repository.exists_for_user(current_user.id)
    
    return BusinessStatsResponse(
        business_settings_configured=settings_exist,
        total_tax_configurations=total_tax_configs,
        active_tax_configurations=active_tax_configs,
        has_default_tax_configuration=default_tax_config is not None,
        default_tax_configuration_id=str(default_tax_config.id) if default_tax_config else None
    )


# Convenience Routes
@router.get("/tax-configurations/active/list", response_model=List[TaxConfigurationResponse])
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_active_tax_configurations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active tax configurations (convenience endpoint for dropdowns)."""
    service = TaxConfigurationService(db)
    configurations, _ = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=1000,  # High limit for dropdowns
        filters={"is_active": True},
        sort_field="name",
        sort_order="asc"
    )
    return [TaxConfigurationResponse.model_validate(config) for config in configurations]


@router.get("/validate", response_model=dict)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def validate_business_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate business setup completeness."""
    business_service = BusinessService(db)
    tax_service = TaxConfigurationService(db)
    
    # Check business settings
    settings_exist = await business_service.repository.exists_for_user(current_user.id)
    
    # Check tax configurations
    total_tax_configs = await tax_service.count(current_user.id, include_inactive=False)
    default_tax_config = await tax_service.get_default_configuration(current_user.id)
    
    validation_results = {
        "business_settings_configured": settings_exist,
        "has_tax_configurations": total_tax_configs > 0,
        "has_default_tax_configuration": default_tax_config is not None,
        "setup_complete": settings_exist and total_tax_configs > 0 and default_tax_config is not None,
        "recommendations": []
    }
    
    # Add recommendations
    if not settings_exist:
        validation_results["recommendations"].append("Configure business settings")
    if total_tax_configs == 0:
        validation_results["recommendations"].append("Create at least one tax configuration")
    if total_tax_configs > 0 and default_tax_config is None:
        validation_results["recommendations"].append("Set a default tax configuration")
    
    return validation_results


# Additional convenience endpoints for business management
@router.get("/settings/exists", response_model=dict)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def check_business_settings_exist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if business settings exist for user."""
    service = BusinessService(db)
    exists = await service.repository.exists_for_user(current_user.id)
    return {"exists": exists}


@router.get("/tax-configurations/summary", response_model=List[dict])
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_tax_configurations_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tax configurations summary for dropdowns."""
    service = TaxConfigurationService(db)
    configurations, _ = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=1000,
        filters={"is_active": True},
        sort_field="name",
        sort_order="asc"
    )
    
    return [
        {
            "id": str(config.id),
            "name": config.name,
            "tax_rate": float(config.tax_rate),
            "is_default": config.is_default
        }
        for config in configurations
    ]