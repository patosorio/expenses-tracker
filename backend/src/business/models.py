from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, JSON, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime

from ..core.database import Base

class BusinessSettings(Base):
    __tablename__ = "business_settings"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Company Information
    company_name = Column(String(200), nullable=True)
    company_email = Column(String(100), nullable=True)
    company_phone = Column(String(20), nullable=True)
    tax_id = Column(String(50), nullable=True)
    website = Column(String(200), nullable=True)
    industry = Column(String(100), nullable=True)
    
    # Address Information
    address_line_1 = Column(String(200), nullable=True)
    address_line_2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(2), default="PT")  # ISO country code
    
    # Business Configuration
    default_currency = Column(String(3), default="EUR")
    fiscal_year_start = Column(String(10), default="01-01")  # MM-DD format
    business_type = Column(String(50), default="service")  # service, retail, saas, restaurant
    employee_count = Column(Integer, nullable=True)
    
    # Financial Settings
    default_payment_terms = Column(Integer, default=30)  # days
    late_fee_percentage = Column(Numeric(5, 2), default=0.00)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="business_settings")
    
    def __repr__(self):
        return f"<BusinessSettings(id={self.id}, user_id={self.user_id})>"

class TaxConfiguration(Base):
    """User-specific tax configuration for automated tax calculations"""
    __tablename__ = "tax_configurations"

    # Primary key with PostgreSQL UUID
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Basic tax fields
    name = Column(String(100), nullable=False)  # "VAT 21%", "IVA 23%"
    rate = Column(Numeric(5, 2), nullable=False)  # Percentage (0.00 to 100.00)
    tax_code = Column(String(20), nullable=True)  # Tax authority code
    is_default = Column(Boolean, default=False)
    country_code = Column(String(2), nullable=True, default="PT")  # ISO country code
    is_active = Column(Boolean, default=True)
    description = Column(String(255), nullable=True)
    
    # Multitenant support
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tax_configurations")
    expenses = relationship("Expense", back_populates="tax_config")
    
    # Table constraints
    __table_args__ = (
        # Tax rate validation
        CheckConstraint(
            'rate >= 0 AND rate <= 100',
            name='ck_tax_rate_range'
        ),
        
        # Only one default tax configuration per user
        UniqueConstraint('user_id', 'is_default', name='uq_default_tax_per_user'),
        
        # Unique tax name per user
        UniqueConstraint('user_id', 'name', name='uq_tax_name_per_user'),
        
        # Performance indexes
        Index('ix_tax_configs_user_active', 'user_id', 'is_active'),
        Index('ix_tax_configs_user_default', 'user_id', 'is_default'),
    )
    
    def __repr__(self):
        return f"<TaxConfiguration(id={self.id}, name={self.name}, rate={self.rate}%)>"

 