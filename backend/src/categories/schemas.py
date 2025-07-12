from datetime import datetime
from typing import Optional, List, Union
from uuid import UUID
import re

from pydantic import BaseModel, field_validator, computed_field

from src.categories.models import CategoryType


class CategoryBase(BaseModel):
    name: str
    type: CategoryType
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: bool = False
    parent_id: Optional[UUID] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Category name cannot be empty')
        if len(v.strip()) > 100:
            raise ValueError('Category name must be 100 characters or less')
        return v.strip()

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be in hex format (#RRGGBB)')
        return v.upper()

    @field_validator('icon')
    @classmethod
    def validate_icon(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError('Icon must be 10 characters or less')
        return v


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category (all fields optional)"""
    name: Optional[str] = None
    type: Optional[CategoryType] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: Optional[bool] = None
    parent_id: Optional[UUID] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError('Category name cannot be empty')
        if len(v.strip()) > 100:
            raise ValueError('Category name must be 100 characters or less')
        return v.strip()

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be in hex format (#RRGGBB)')
        return v.upper()

    @field_validator('icon')
    @classmethod
    def validate_icon(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError('Icon must be 10 characters or less')
        return v


class CategoryResponse(CategoryBase):
    """Schema for category API responses"""
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    level: int = 0

    class Config:
        from_attributes = True


class CategoryWithChildren(CategoryResponse):
    """Schema for category with children relationships"""
    children: List['CategoryWithChildren'] = []

    class Config:
        from_attributes = True


class CategoryHierarchy(BaseModel):
    """Schema for hierarchical category tree responses"""
    id: UUID
    name: str
    type: CategoryType
    color: Optional[str] = None
    icon: Optional[str] = None
    level: int
    path: List[str]  # Breadcrumb path from root to this category
    children: List['CategoryHierarchy'] = []

    class Config:
        from_attributes = True


class CategoryPath(BaseModel):
    """Schema for category breadcrumb path"""
    category_id: UUID
    path: List[CategoryResponse]
    path_names: List[str]


class CategoryListResponse(BaseModel):
    """Schema for paginated category list responses"""
    categories: List[CategoryResponse]
    total: int
    page: int
    per_page: int
    pages: int


class CategoryStatsResponse(BaseModel):
    """Schema for category statistics"""
    total_categories: int
    expense_categories: int
    income_categories: int
    root_categories: int
    categories_by_type: dict[CategoryType, int]
    max_depth: int


# Enable forward references for recursive models
CategoryWithChildren.model_rebuild()
CategoryHierarchy.model_rebuild()
