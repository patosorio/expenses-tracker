from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
from uuid import UUID

class BusinessSettingsBase(BaseModel):
    company_name: Optional[str] = Field(None, max_length=200)
    company_email: Optional[EmailStr] = None
    company_phone: Optional[str] = Field(None, max_length=20)
    tax_id: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    
    # Address
    address_line_1: Optional[str] = Field(None, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="PT", max_length=2)
    
    # Business Config
    default_currency: str = Field(default="EUR", max_length=3)
    fiscal_year_start: str = Field(default="01-01", pattern=r"^\d{2}-\d{2}$")
    business_type: str = Field(default="service", max_length=50)
    employee_count: Optional[int] = Field(None, ge=1)
    
    # Financial
    default_payment_terms: int = Field(default=30, ge=1, le=365)
    late_fee_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)

class BusinessSettingsCreate(BusinessSettingsBase):
    pass

class BusinessSettingsUpdate(BaseModel):
    # All fields optional for partial updates
    company_name: Optional[str] = Field(None, max_length=200)
    company_email: Optional[EmailStr] = None
    company_phone: Optional[str] = Field(None, max_length=20)
    tax_id: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    address_line_1: Optional[str] = Field(None, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)
    default_currency: Optional[str] = Field(None, max_length=3)
    fiscal_year_start: Optional[str] = Field(None, pattern=r"^\d{2}-\d{2}$")
    business_type: Optional[str] = Field(None, max_length=50)
    employee_count: Optional[int] = Field(None, ge=1)
    default_payment_terms: Optional[int] = Field(None, ge=1, le=365)
    late_fee_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

class BusinessSettingsResponse(BusinessSettingsBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Tax Configuration Schemas
class TaxConfigurationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rate: Decimal = Field(..., ge=0, le=100)
    tax_code: Optional[str] = Field(None, max_length=20)
    country_code: str = Field(default="PT", max_length=2)
    is_default: bool = False
    is_active: bool = True
    description: Optional[str] = Field(None, max_length=255)

class TaxConfigurationCreate(TaxConfigurationBase):
    pass

class TaxConfigurationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_code: Optional[str] = Field(None, max_length=20)
    country_code: Optional[str] = Field(None, max_length=2)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=255)

class TaxConfigurationResponse(TaxConfigurationBase):
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 