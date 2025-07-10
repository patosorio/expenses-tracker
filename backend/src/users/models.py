from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()
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
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
