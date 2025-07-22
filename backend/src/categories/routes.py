from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import math

from .models import Category, CategoryType
from .schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryHierarchy,
    CategoryPath, CategoryListResponse, CategoryStatsResponse
)
from .service import CategoryService
from ..auth.dependencies import get_current_user
from ..core.database import get_db
from ..users.models import User

router = APIRouter()


@router.post("/", response_model=CategoryResponse, status_code=201)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category with comprehensive validation."""
    category_service = CategoryService(db)
    category = await category_service.create_category(current_user.id, category_data)
    
    # Build response with computed level
    response = CategoryResponse.model_validate(category)
    response.level = category.get_level() if hasattr(category, 'get_level') else 0
    return response


@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category ID"),
    search: Optional[str] = Query(None, description="Search categories by name"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get categories with filtering and pagination."""
    category_service = CategoryService(db)
    categories, total = await category_service.get_categories(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        category_type=type,
        parent_id=parent_id,
        search=search,
        include_inactive=include_inactive
    )
    
    # Build response list with computed levels
    category_responses = []
    for category in categories:
        response = CategoryResponse.model_validate(category)
        response.level = category.get_level() if hasattr(category, 'get_level') else 0
        category_responses.append(response)
    
    return CategoryListResponse(
        categories=category_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        per_page=limit,
        pages=math.ceil(total / limit) if total > 0 and limit > 0 else 0
    )


@router.get("/hierarchy", response_model=List[CategoryHierarchy])
async def get_category_hierarchy(
    type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get hierarchical tree structure of categories."""
    category_service = CategoryService(db)
    hierarchy = await category_service.get_category_hierarchy(
        user_id=current_user.id,
        category_type=type,
        include_inactive=include_inactive
    )
    return hierarchy


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single category by ID."""
    category_service = CategoryService(db)
    category = await category_service.get_category_by_id(category_id, current_user.id)
    
    # Service layer handles the not found case
    response = CategoryResponse.model_validate(category)
    response.level = category.get_level() if hasattr(category, 'get_level') else 0
    return response


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a category with comprehensive validation."""
    category_service = CategoryService(db)
    category = await category_service.update_category(
        category_id=category_id,
        user_id=current_user.id,
        category_data=category_data
    )
    
    response = CategoryResponse.model_validate(category)
    response.level = category.get_level() if hasattr(category, 'get_level') else 0
    return response


@router.delete("/{category_id}")
async def delete_category(
    category_id: UUID,
    cascade: bool = Query(False, description="Cascade delete to children"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a category with optional cascade."""
    category_service = CategoryService(db)
    await category_service.delete_category(
        category_id=category_id,
        user_id=current_user.id,
        cascade=cascade
    )
    
    return {
        "message": "Category deleted successfully",
        "category_id": str(category_id),
        "cascade": cascade
    }


@router.get("/{category_id}/path", response_model=CategoryPath)
async def get_category_path(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get category breadcrumb path from root to category."""
    category_service = CategoryService(db)
    path = await category_service.get_category_path(category_id, current_user.id)
    return path


@router.get("/{category_id}/children", response_model=List[CategoryResponse])
async def get_category_children(
    category_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get direct children of a category."""
    category_service = CategoryService(db)
    
    # Service layer will validate parent category exists
    children = await category_service.get_children(
        category_id=category_id,
        user_id=current_user.id,
        include_inactive=include_inactive
    )
    
    # Build response list with computed levels
    children_responses = []
    for child in children:
        response = CategoryResponse.model_validate(child)
        response.level = child.get_level() if hasattr(child, 'get_level') else 0
        children_responses.append(response)
    
    return children_responses


@router.get("/stats/overview", response_model=CategoryStatsResponse)
async def get_category_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get category statistics for the user."""
    category_service = CategoryService(db)
    stats = await category_service.get_category_stats(current_user.id)
    return stats


# Additional convenience endpoints for category management

@router.get("/types/{category_type}", response_model=CategoryListResponse)
async def get_categories_by_type(
    category_type: CategoryType,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all categories of a specific type (convenience endpoint)."""
    category_service = CategoryService(db)
    categories, total = await category_service.get_categories(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        category_type=category_type,
        include_inactive=include_inactive
    )
    
    category_responses = []
    for category in categories:
        response = CategoryResponse.model_validate(category)
        response.level = category.get_level() if hasattr(category, 'get_level') else 0
        category_responses.append(response)
    
    return CategoryListResponse(
        categories=category_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        per_page=limit,
        pages=math.ceil(total / limit) if total > 0 and limit > 0 else 0
    )


@router.get("/root/list", response_model=List[CategoryResponse])
async def get_root_categories(
    type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get only root categories (convenience endpoint for dropdowns)."""
    category_service = CategoryService(db)
    categories, _ = await category_service.get_categories(
        user_id=current_user.id,
        skip=0,
        limit=1000,  # High limit for root categories
        category_type=type,
        parent_id=None,  # Only root categories
        include_inactive=include_inactive
    )
    
    category_responses = []
    for category in categories:
        response = CategoryResponse.model_validate(category)
        response.level = 0  # Root categories are always level 0
        category_responses.append(response)
    
    return category_responses


@router.post("/{category_id}/archive")
async def archive_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive a category (soft delete without cascade)."""
    category_service = CategoryService(db)
    await category_service.delete_category(
        category_id=category_id,
        user_id=current_user.id,
        cascade=False
    )
    
    return {
        "message": "Category archived successfully",
        "category_id": str(category_id)
    }


# TODO: Implement restore category service
# @router.post("/{category_id}/restore")
# async def restore_category(
#     category_id: UUID,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Restore an archived category (if you implement this in service)."""
#     category_service = CategoryService(db)
    
#     return {
#         "message": "Category restore endpoint - implement in service layer",
#         "category_id": str(category_id)
#     }