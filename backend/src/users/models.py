from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum

from src.database import Base

class UserRole(str, PyEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"

class UserStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    
    # Authentication fields
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.ADMIN)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    
    # Profile fields
    timezone = Column(String, default="CET")
    language = Column(String, default="en")

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Business fields: personal or business option
    user_type = Column(String(20), nullable=False, default="personal")
    company = Column(String(255))
    
    # Relationships
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    business_settings = relationship("BusinessSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tax_configurations = relationship("TaxConfiguration", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Enhanced Preferences (expand beyond basic timezone/language in User model)
    currency = Column(String(3), default="EUR")
    date_format = Column(String(20), default="DD/MM/YYYY")
    time_format = Column(String(10), default="24h")  # 12h or 24h
    week_start = Column(String(10), default="monday")  # monday or sunday
    theme = Column(String(10), default="system")  # light, dark, system
    fiscal_year_start = Column(String(10), default="01-01")  # MM-DD format
    
    # Notification Preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    bill_reminders = Column(Boolean, default=True)
    weekly_reports = Column(Boolean, default=False)
    overdue_invoices = Column(Boolean, default=True)
    team_updates = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    expense_summaries = Column(Boolean, default=True)
    budget_alerts = Column(Boolean, default=True)
    
    # Data Export Preferences
    default_export_format = Column(String(10), default="csv")  # csv, excel, pdf
    include_attachments = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<UserSettings(id={self.id}, user_id={self.user_id})>"
