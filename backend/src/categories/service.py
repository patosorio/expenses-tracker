from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from .models import Category, CategoryType
from .repository import CategoryRepository
from .schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryHierarchy,
    CategoryPath, CategoryStatsResponse, CategoryWithChildren
)
from ..core.database import get_db
from .exceptions import (
    CategoryNotFoundError, CategoryValidationError, CategoryAlreadyExistsError,
    InvalidCategoryParentError, CategoryTypeConflictError, CircularCategoryReferenceError,
    CategoryDeleteError, CategoryUpdateError, InvalidCategoryHierarchyError
)

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, db: AsyncSession = None):
        self.db = db or next(get_db())
        self.category_repo = CategoryRepository(self.db)

    async def create_category(self, user_id: str, category_data: CategoryCreate) -> Category:
        """Create a new category with validation"""
        try:
            # Business logic: Validate parent if provided
            if category_data.parent_id:
                parent_category = await self.category_repo.get_by_id(category_data.parent_id, user_id)
                if not parent_category:
                    raise InvalidCategoryParentError("Parent category not found")
                
                # Business logic: Ensure parent and child have same type
                if parent_category.type != category_data.type:
                    raise CategoryTypeConflictError(
                        f"Parent category type ({parent_category.type}) must match child type ({category_data.type})"
                    )

            # Business logic: Check for duplicate name at the same level
            is_duplicate = await self.category_repo.check_duplicate_name(
                user_id, category_data.name, category_data.parent_id
            )
            
            if is_duplicate:
                raise CategoryAlreadyExistsError(
                    f"Category '{category_data.name}' already exists at this level"
                )

            # Business logic: Create new category
            category = Category(
                user_id=user_id,
                **category_data.model_dump()
            )

            # Delegate to repository for data access
            return await self.category_repo.create(category)
            
        except Exception as e:
            logger.error(f"Error creating category for user {user_id}: {str(e)}")
            raise

    async def get_category_hierarchy(
        self, 
        user_id: str, 
        category_type: Optional[CategoryType] = None,
        include_inactive: bool = False
    ) -> List[CategoryHierarchy]:
        """Build hierarchical tree structure from root categories"""
        try:
            # Delegate to repository for data access
            return await self.category_repo.get_hierarchy(user_id, category_type, include_inactive)
        except Exception as e:
            logger.error(f"Error getting category hierarchy for user {user_id}: {str(e)}")
            raise

    async def get_category_path(self, category_id: UUID, user_id: str) -> CategoryPath:
        """Generate breadcrumb path from root to category"""
        try:
            # Delegate to repository for data access
            return await self.category_repo.get_path(category_id, user_id)
        except Exception as e:
            logger.error(f"Error getting category path for category {category_id}: {str(e)}")
            raise

    async def update_category(
        self, 
        category_id: UUID, 
        user_id: str, 
        category_data: CategoryUpdate
    ) -> Category:
        """Update category with validation"""
        try:
            category = await self.category_repo.get_by_id(category_id, user_id)
            if not category:
                raise CategoryNotFoundError("Category not found")
            
            # Business logic: Handle parent change validation
            if category_data.parent_id is not None:
                if category_data.parent_id == category.id:
                    raise CircularCategoryReferenceError("Category cannot be its own parent")
                
                if category_data.parent_id:
                    # Check if new parent exists
                    new_parent = await self.category_repo.get_by_id(category_data.parent_id, user_id)
                    if not new_parent:
                        raise InvalidCategoryParentError("New parent category not found")
                    
                    # Check for circular reference
                    if await self.category_repo.check_circular_reference(category.id, category_data.parent_id, user_id):
                        raise CircularCategoryReferenceError("This change would create a circular reference")
                    
                    # Ensure type compatibility
                    category_type = category_data.type or category.type
                    if new_parent.type != category_type:
                        raise CategoryTypeConflictError("Parent and child categories must have the same type")

            # Business logic: Check for duplicate name if name is being changed
            if category_data.name and category_data.name != category.name:
                parent_id = category_data.parent_id if category_data.parent_id is not None else category.parent_id
                is_duplicate = await self.category_repo.check_duplicate_name(
                    user_id, category_data.name, parent_id, category_id
                )
                
                if is_duplicate:
                    raise CategoryAlreadyExistsError(
                        f"Category '{category_data.name}' already exists at this level"
                    )

            # Business logic: Update fields
            for field, value in category_data.model_dump(exclude_unset=True).items():
                setattr(category, field, value)
            
            # Delegate to repository for data access
            return await self.category_repo.update(category)
            
        except Exception as e:
            logger.error(f"Error updating category {category_id} for user {user_id}: {str(e)}")
            raise CategoryUpdateError(f"Failed to update category: {str(e)}")

    async def delete_category(
        self, 
        category_id: UUID, 
        user_id: str, 
        cascade: bool = False
    ) -> None:
        """Soft delete category with optional cascade for children"""
        try:
            category = await self.category_repo.get_by_id(category_id, user_id)
            if not category:
                raise CategoryNotFoundError("Category not found")
            
            # Business logic: Handle cascade deletion
            if cascade:
                # Recursively soft delete all descendants
                descendants = category.get_descendants()
                for descendant in descendants:
                    descendant.is_active = False
            else:
                # Check if category has active children
                active_children = await self.category_repo.get_children(category_id, user_id, include_inactive=False)
                
                if len(active_children) > 0:
                    raise InvalidCategoryParentError(
                        "Cannot delete category with active children. Use cascade=True or move children first."
                    )
            
            # Delegate to repository for data access
            await self.category_repo.delete(category)
            
        except Exception as e:
            logger.error(f"Error deleting category {category_id} for user {user_id}: {str(e)}")
            raise CategoryDeleteError(f"Failed to delete category: {str(e)}")

    async def get_categories(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        category_type: Optional[CategoryType] = None,
        parent_id: Optional[UUID] = None,
        search: Optional[str] = None,
        include_inactive: bool = False
    ) -> Tuple[List[Category], int]:
        """Get categories with filtering and pagination"""
        try:
            # Delegate to repository for data access
            return await self.category_repo.get_categories(
                user_id, skip, limit, category_type, parent_id, search, include_inactive
            )
        except Exception as e:
            logger.error(f"Error getting categories for user {user_id}: {str(e)}")
            raise

    async def get_category_by_id(self, category_id: UUID, user_id: str) -> Optional[Category]:
        """Get category by ID for the user"""
        try:
            # Delegate to repository for data access
            return await self.category_repo.get_by_id(category_id, user_id)
        except Exception as e:
            logger.error(f"Error getting category {category_id} for user {user_id}: {str(e)}")
            raise

    async def get_children(
        self, 
        category_id: UUID, 
        user_id: str, 
        include_inactive: bool = False
    ) -> List[Category]:
        """Get direct children of a category"""
        try:
            # Delegate to repository for data access
            return await self.category_repo.get_children(category_id, user_id, include_inactive)
        except Exception as e:
            logger.error(f"Error getting children for category {category_id}: {str(e)}")
            raise

    async def get_category_stats(self, user_id: str) -> CategoryStatsResponse:
        """Get category statistics for the user"""
        try:
            # Delegate to repository for data access
            return await self.category_repo.get_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting category stats for user {user_id}: {str(e)}")
            raise


