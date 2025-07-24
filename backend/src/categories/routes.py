from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from .models import CategoryType
from .schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryHierarchy,
    CategoryPath,
    CategoryStatsResponse
)
from .service import CategoryService
from ..auth.dependencies import get_current_user
from ..core.database import get_db
from ..users.models import User
from ..core.shared.decorators import api_endpoint
from ..core.shared.pagination import (
    create_legacy_category_response,
    CategoryListResponse
)

router = APIRouter()


@router.post("/", response_model=CategoryResponse, status_code=201)
@api_endpoint(handle_exceptions=True, log_calls=True)
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
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_categories(
    # Pagination parameters
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    
    # Filter parameters
    type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category ID"),
    search: Optional[str] = Query(None, description="Search categories by name"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    
    # Sort parameters
    sort_by: str = Query("name", regex="^(name|created_at|updated_at)$", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get categories with filtering and pagination."""
    service = CategoryService(db)

    # Build filters
    filters = {}
    if type:
        filters['type'] = type
    if parent_id:
        filters['parent_id'] = parent_id

    # Get paginated results
    categories, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
        search=search,
        sort_field=sort_by,
        sort_order=sort_order,
        filters=filters
    )
    
    # Build response list with computed levels
    category_responses = []
    for category in categories:
        response = CategoryResponse.model_validate(category)
        response.level = category.get_level() if hasattr(category, 'get_level') else 0
        category_responses.append(response)
    
    return create_legacy_category_response(category_responses, total, skip, limit)


@router.get("/hierarchy", response_model=List[CategoryHierarchy])
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_category_hierarchy(
    type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get hierarchical tree structure of categories."""
    service = CategoryService(db)
    return await service.get_category_hierarchy(
        user_id=current_user.id,
        category_type=type,
        include_inactive=include_inactive
    )


@router.get("/{category_id}", response_model=CategoryResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single category by ID."""
    service = CategoryService(db)
    category = await service.get_category_by_id_or_raise(category_id, current_user.id)
    
    # Service layer handles the not found case
    response = CategoryResponse.model_validate(category)
    response.level = category.get_level() if hasattr(category, 'get_level') else 0
    return response


@router.put("/{category_id}", response_model=CategoryResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a category with comprehensive validation."""
    service = CategoryService(db)
    category = await service.update_category(category_id, current_user.id, category_data)
    
    response = CategoryResponse.model_validate(category)
    response.level = category.get_level() if hasattr(category, 'get_level') else 0
    return response


@router.delete("/{category_id}")
@api_endpoint(handle_exceptions=True, log_calls=True)
async def delete_category(
    category_id: UUID,
    cascade: bool = Query(False, description="Cascade delete to children"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a category with optional cascade."""
    service = CategoryService(db)
    await service.delete_category(category_id, current_user.id, cascade)
    
    return {
        "message": "Category deleted successfully",
        "category_id": str(category_id),
        "cascade": cascade
    }


@router.get("/{category_id}/path", response_model=CategoryPath)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_category_path(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get category breadcrumb path from root to category."""
    service = CategoryService(db)
    return await service.get_category_path(category_id, current_user.id)


@router.get("/{category_id}/children", response_model=List[CategoryResponse])
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_category_children(
    category_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get direct children of a category."""
    service = CategoryService(db)
    children = await service.get_children(category_id, current_user.id, include_inactive)
    
    # Service layer will validate parent category exists
    children = await service.get_children(
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
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_category_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get category statistics for the user."""
    service = CategoryService(db)
    return await service.get_category_stats(current_user.id)


# Additional convenience endpoints for category management

@router.get("/types/{category_type}", response_model=CategoryListResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_categories_by_type(
    category_type: CategoryType,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all categories of a specific type (convenience endpoint)."""
    service = CategoryService(db)
    categories, total = await service.get_categories(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
        filters={"type": category_type}
    )
    
    category_responses = []
    for category in categories:
        response = CategoryResponse.model_validate(category)
        response.level = category.get_level() if hasattr(category, 'get_level') else 0
        category_responses.append(response)
    
    return create_legacy_category_response(category_responses, total, skip, limit)


@router.get("/root/list", response_model=List[CategoryResponse])
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_root_categories(
    type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get only root categories (convenience endpoint for dropdowns)."""
    service = CategoryService(db)

    filters = {"parent_id": None}  # Only root categories
    if type:
        filters["type"] = type

    categories, _ = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=1000,  # High limit for root categories
        include_inactive=include_inactive,
        filters=filters
    )
    
    category_responses = []
    for category in categories:
        response = CategoryResponse.model_validate(category)
        response.level = 0  # Root categories are always level 0
        category_responses.append(response)
    
    return category_responses


@router.post("/{category_id}/archive")
@api_endpoint(handle_exceptions=True, log_calls=True)
async def archive_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive a category (soft delete without cascade)."""
    service = CategoryService(db)
    await service.delete(category_id, current_user.id, soft=True)
    
    return {
        "message": "Category archived successfully",
        "category_id": str(category_id)
    }


# TODO: Implement restore category service
# @router.post("/{category_id}/restore")
# @api_endpoint(handle_exceptions=True, log_calls=True)
# async def restore_category(
#     category_id: UUID,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Restore an archived category."""
#     service = CategoryService(db)
    
#     # Simply update the category to active - let the service/decorator handle errors
#     await service.update(category_id, {"is_active": True}, current_user.id)
    
#     return {
#         "message": "Category restored successfully",
#         "category_id": str(category_id)
#     }
