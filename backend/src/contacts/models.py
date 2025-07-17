from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, CheckConstraint, Index, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import text
from enum import Enum as PyEnum

from src.database import Base


class ContactType(str, PyEnum):
    CLIENT = "CLIENT"
    VENDOR = "VENDOR"
    SUPPLIER = "SUPPLIER"


class Contact(Base):
    """Contact model for vendors, suppliers, and clients"""
    __tablename__ = "contacts"

    # Primary key with PostgreSQL UUID
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Basic contact information
    name = Column(String(200), nullable=False)
    contact_type = Column(String(20), nullable=False, index=True)
    
    # Contact details
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(2), nullable=False, default='PT')  # ISO country code
    
    # Tax information
    tax_number = Column(String(50), nullable=True)
    
    # Business information
    website = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of strings
    custom_fields = Column(JSON, nullable=True)  # Flexible custom data
    
    # Multitenant support
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User")
    expenses = relationship("Expense", back_populates="contact")
    
    # Table constraints
    __table_args__ = (
        # Email validation
        CheckConstraint(
            "email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name='ck_contact_email_format'
        ),
        
        # Country code validation (ISO 3166-1 alpha-2)
        CheckConstraint(
            "country ~ '^[A-Z]{2}$'",
            name='ck_contact_country_format'
        ),
        
        # Contact type validation
        CheckConstraint(
            "contact_type IN ('CLIENT', 'VENDOR', 'SUPPLIER')",
            name='ck_contact_type_valid'
        ),
        
        # Performance indexes
        Index('ix_contacts_user_type', 'user_id', 'contact_type'),
        Index('ix_contacts_user_name', 'user_id', 'name'),
        Index('ix_contacts_user_active', 'user_id', 'is_active'),
        Index('ix_contacts_email', 'email'),
    )
    
    def __repr__(self):
        return f"<Contact(id={self.id}, name={self.name}, type={self.contact_type})>"
    
    @property
    def full_address(self) -> str:
        """Return formatted full address"""
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state_province,
            self.postal_code,
            self.country
        ]
        return ", ".join(part for part in address_parts if part)
