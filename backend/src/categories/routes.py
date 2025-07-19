from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import math

from .models import Category, CategoryType
from .schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryHierarchy,
    CategoryPath, CategoryListResponse, CategoryStatsResponse,
    CategoryWithChildren
)
from .service import CategoryService
from ..auth.dependencies import get_current_user
from ..core.database import get_db
from ..users.models import User
from .exceptions import (
    CategoryNotFoundError, CategoryAlreadyExistsError, InvalidCategoryParentError,
    CategoryTypeConflictError, CircularCategoryReferenceError
)

router = APIRouter()


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category"""
    try:
        category_service = CategoryService(db)
        category = await category_service.create_category(current_user.id, category_data)
        
        # Calculate level for response
        response = CategoryResponse.model_validate(category)
        response.level = category.get_level()
        return response
        
    except (CategoryAlreadyExistsError, InvalidCategoryParentError, CategoryTypeConflictError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {str(e)}"
        )


@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category ID"),
    search: Optional[str] = Query(None, description="Search categories by name"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get categories with filtering and pagination"""
    try:
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
        
        # Add level calculation to response
        category_responses = []
        for category in categories:
            response = CategoryResponse.model_validate(category)
            response.level = category.get_level()
            category_responses.append(response)
        
        return CategoryListResponse(
            categories=category_responses,
            total=total,
            page=skip // limit + 1,
            per_page=limit,
            pages=math.ceil(total / limit) if total > 0 else 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )


@router.get("/hierarchy", response_model=List[CategoryHierarchy])
async def get_category_hierarchy(
    type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get hierarchical tree structure of categories"""
    try:
        category_service = CategoryService(db)
        hierarchy = await category_service.get_category_hierarchy(
            user_id=current_user.id,
            category_type=type,
            include_inactive=include_inactive
        )
        return hierarchy
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category hierarchy: {str(e)}"
        )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single category by ID"""
    try:
        category_service = CategoryService(db)
        category = await category_service.get_category_by_id(category_id, current_user.id)
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        response = CategoryResponse.model_validate(category)
        response.level = category.get_level()
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category: {str(e)}"
        )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a category"""
    try:
        category_service = CategoryService(db)
        category = await category_service.update_category(
            category_id=category_id,
            user_id=current_user.id,
            category_data=category_data
        )
        
        response = CategoryResponse.model_validate(category)
        response.level = category.get_level()
        return response
        
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    except (
        CategoryAlreadyExistsError, 
        InvalidCategoryParentError, 
        CategoryTypeConflictError,
        CircularCategoryReferenceError
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category: {str(e)}"
        )


@router.delete("/{category_id}")
async def delete_category(
    category_id: UUID,
    cascade: bool = Query(False, description="Cascade delete to children"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a category"""
    try:
        category_service = CategoryService(db)
        await category_service.delete_category(
            category_id=category_id,
            user_id=current_user.id,
            cascade=cascade
        )
        
        return {"message": "Category deleted successfully"}
        
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    except InvalidCategoryParentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete category: {str(e)}"
        )


@router.get("/{category_id}/path", response_model=CategoryPath)
async def get_category_path(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get category breadcrumb path from root to category"""
    try:
        category_service = CategoryService(db)
        path = await category_service.get_category_path(category_id, current_user.id)
        return path
        
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category path: {str(e)}"
        )


@router.get("/{category_id}/children", response_model=List[CategoryResponse])
async def get_category_children(
    category_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get direct children of a category"""
    try:
        # First verify the parent category exists and belongs to user
        category_service = CategoryService(db)
        parent_category = await category_service.get_category_by_id(category_id, current_user.id)
        
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )
        
        children = await category_service.get_children(
            category_id=category_id,
            user_id=current_user.id,
            include_inactive=include_inactive
        )
        
        # Add level calculation to responses
        children_responses = []
        for child in children:
            response = CategoryResponse.model_validate(child)
            response.level = child.get_level()
            children_responses.append(response)
        
        return children_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category children: {str(e)}"
        )


@router.get("/stats/overview", response_model=CategoryStatsResponse)
async def get_category_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get category statistics for the user"""
    try:
        category_service = CategoryService(db)
        stats = await category_service.get_category_stats(current_user.id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category statistics: {str(e)}"
        )
