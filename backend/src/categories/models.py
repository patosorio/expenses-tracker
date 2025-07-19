from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import text
from datetime import datetime
from enum import Enum as PyEnum

from ..core.database import Base


class CategoryType(str, PyEnum):
    EXPENSE = "expense"
    INCOME = "income"


class Category(Base):
    __tablename__ = "categories"

    # Primary key with PostgreSQL UUID
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )
    
    # Basic fields
    name = Column(String(100), nullable=False)
    type = Column(Enum(CategoryType), nullable=False)
    color = Column(String(7), nullable=True)  # Hex color format #RRGGBB
    icon = Column(String(10), nullable=True)  # Emoji icon
    is_default = Column(Boolean, default=False)
    
    # Multitenant support
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Hierarchical structure
    parent_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="categories")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    
    # Table constraints
    __table_args__ = (
        # Unique constraint on (user_id, name, parent_id) to prevent duplicate names at same level
        UniqueConstraint('user_id', 'name', 'parent_id', name='uq_category_name_per_level'),
        
        # Check constraint for type validation
        CheckConstraint(
            type.in_(['expense', 'income']),
            name='ck_category_type'
        ),
        
        # Check constraint for color format (hex color)
        CheckConstraint(
            "color IS NULL OR color ~ '^#[0-9A-Fa-f]{6}$'",
            name='ck_category_color_format'
        ),
        
        # Prevent self-referencing parent_id
        CheckConstraint(
            'id != parent_id',
            name='ck_category_no_self_reference'
        ),
        
        # Additional index for performance
        Index('ix_categories_user_parent', 'user_id', 'parent_id'),
        Index('ix_categories_user_type', 'user_id', 'type'),
    )
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, type={self.type}, user_id={self.user_id})>"
    
    def get_level(self) -> int:
        """Calculate the level/depth of this category in the hierarchy"""
        level = 0
        current = self
        while current.parent_id:
            level += 1
            current = current.parent
        return level
    
    def get_ancestors(self) -> list['Category']:
        """Get all ancestor categories from root to this category"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_descendants(self) -> list['Category']:
        """Get all descendant categories recursively"""
        descendants = []
        for child in self.children:
            if child.is_active:
                descendants.append(child)
                descendants.extend(child.get_descendants())
        return descendants
