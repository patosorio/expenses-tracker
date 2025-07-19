from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .models import BusinessSettings, TaxConfiguration
from .schemas import (
    BusinessSettingsResponse, BusinessSettingsUpdate,
    TaxConfigurationResponse, TaxConfigurationCreate, TaxConfigurationUpdate
)
from .service import BusinessService
from ..auth.dependencies import get_current_user
from ..users.models import User
from ..core.database import get_db
from .exceptions import BusinessSettingsNotFoundError, TaxConfigurationNotFoundError

router = APIRouter()

# Business Settings Routes
@router.get("/settings", response_model=BusinessSettingsResponse)
async def get_business_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get business settings"""
    try:
        business_service = BusinessService(db)
        settings = await business_service.get_business_settings(current_user.id)
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get business settings: {str(e)}"
        )

@router.put("/settings", response_model=BusinessSettingsResponse)
async def update_business_settings(
    settings_data: BusinessSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update business settings"""
    try:
        business_service = BusinessService(db)
        settings = await business_service.update_business_settings(
            current_user.id, settings_data
        )
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update business settings: {str(e)}"
        )

# Tax Configuration Routes
@router.get("/tax-configs", response_model=List[TaxConfigurationResponse])
async def get_tax_configurations(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tax configurations"""
    try:
        business_service = BusinessService(db)
        configs = await business_service.get_tax_configurations(
            current_user.id, active_only
        )
        return configs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tax configurations: {str(e)}"
        )

@router.get("/tax-configs/{tax_id}", response_model=TaxConfigurationResponse)
async def get_tax_configuration(
    tax_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific tax configuration"""
    try:
        business_service = BusinessService(db)
        config = await business_service.get_tax_configuration(tax_id, current_user.id)
        return config
    except TaxConfigurationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tax configuration: {str(e)}"
        )

@router.post("/tax-configs", response_model=TaxConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_configuration(
    tax_data: TaxConfigurationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create tax configuration"""
    try:
        business_service = BusinessService(db)
        config = await business_service.create_tax_configuration(
            current_user.id, tax_data
        )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tax configuration: {str(e)}"
        )

@router.put("/tax-configs/{tax_id}", response_model=TaxConfigurationResponse)
async def update_tax_configuration(
    tax_id: str,
    tax_data: TaxConfigurationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update tax configuration"""
    try:
        business_service = BusinessService(db)
        config = await business_service.update_tax_configuration(
            tax_id, current_user.id, tax_data
        )
        return config
    except TaxConfigurationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tax configuration: {str(e)}"
        )

@router.delete("/tax-configs/{tax_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tax_configuration(
    tax_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete tax configuration (soft delete)"""
    try:
        business_service = BusinessService(db)
        await business_service.delete_tax_configuration(tax_id, current_user.id)
    except TaxConfigurationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tax configuration: {str(e)}"
        ) 