"""
Categories module for hierarchical category management.

This module provides:
- Category model with unlimited depth hierarchical structure
- Comprehensive business logic for category operations
- RESTful API endpoints with full CRUD functionality
- Multitenant support with user isolation
- Tree traversal and path generation utilities
"""

from .models import Category, CategoryType
from .schemas import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryHierarchy,
    CategoryPath,
    CategoryListResponse,
    CategoryStatsResponse,
    CategoryWithChildren
)
from .service import CategoryService
from .routes import router

__all__ = [
    # Models
    "Category",
    "CategoryType",
    
    # Schemas
    "CategoryBase",
    "CategoryCreate", 
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryHierarchy",
    "CategoryPath",
    "CategoryListResponse",
    "CategoryStatsResponse",
    "CategoryWithChildren",
    
    # Service
    "CategoryService",
    
    # Router
    "router",
]
