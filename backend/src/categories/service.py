from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from ..core.database import get_db
from .models import Category, CategoryType
from .repository import CategoryRepository
from .schemas import *
from .exceptions import *
from ..core.shared.exceptions import ValidationError, InternalServerError

logger = logging.getLogger(__name__)

# Business constants
MAX_CATEGORY_DEPTH = 5
MAX_CATEGORY_NAME_LENGTH = 100


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.category_repo = CategoryRepository(db)

    async def create_category(self, user_id: str, category_data: CategoryCreate) -> Category:
        """Create a new category with validation"""
        try:
            await self._validate_category_data(user_id, category_data)
            
            # Validate parent if provided
            if category_data.parent_id:
                parent_category = await self._validate_parent_category(
                    category_data.parent_id, user_id, category_data.type
                )
                # Check hierarchy depth
                await self._validate_hierarchy_depth(category_data.parent_id, user_id)
                

            # Check for duplicate name at the same level
            await self._check_duplicate_name(
                user_id,
                category_data.name,
                category_data.parent_id
            )
            
            # Create category instance
            category = Category(
                user_id=user_id,
                **category_data.model_dump()
            )

            # Delegate to repository
            created_category = await self.category_repo.create(category)
            logger.info(f"Category created successfully: {created_category.id} for user {user_id}")
            return created_category
            
        except (
            CategoryValidationError, CategoryAlreadyExistsError, InvalidCategoryParentError,
            CategoryTypeConflictError, CategoryDepthLimitExceededError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating category for user {user_id}: {str(e)}", exc_info=True)
            raise InternalServerError(
                detail="Failed to create category due to internal error",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_category_hierarchy(
        self, 
        user_id: str, 
        category_type: Optional[CategoryType] = None,
        include_inactive: bool = False
    ) -> List[CategoryHierarchy]:
        """Build hierarchical tree structure from root categories."""
        try:
            return await self.category_repo.get_hierarchy(user_id, category_type, include_inactive)
        except Exception as e:
            logger.error(f"Error getting category hierarchy for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve category hierarchy",
                context={"user_id": user_id, "category_type": category_type, "original_error": str(e)}
            )

    async def get_category_path(self, category_id: UUID, user_id: str) -> CategoryPath:
        """Generate breadcrumb path from root to category."""
        try:
            # Ensure category exists and belongs to user
            await self._get_category_or_raise(category_id, user_id)
            
            return await self.category_repo.get_path(category_id, user_id)
        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting category path for category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to get category path",
                context={"category_id": str(category_id), "user_id": user_id, "original_error": str(e)}
            )

    async def update_category(
        self, 
        category_id: UUID, 
        user_id: str, 
        category_data: CategoryUpdate
    ) -> Category:
        """Update category with comprehensive validation."""
        try:
            # Get existing category
            category = await self._get_category_or_raise(category_id, user_id)
            
            # Validate update data
            update_fields = category_data.model_dump(exclude_unset=True)
            if not update_fields:
                raise CategoryValidationError(
                    detail="No valid fields provided for update",
                    context={"category_id": str(category_id), "user_id": user_id}
                )
            
            # Check if trying to modify default category
            if category.is_default and any(field in update_fields for field in ['name', 'type', 'parent_id']):
                raise DefaultCategoryModificationError(
                    detail="Cannot modify core properties of default system category",
                    context={"category_id": str(category_id), "is_default": True}
                )
            
            # Validate parent change if specified
            if 'parent_id' in update_fields:
                await self._validate_parent_change(category, category_data.parent_id, user_id)
            
            # Validate name change if specified
            if 'name' in update_fields and update_fields['name'] != category.name:
                parent_id = update_fields.get('parent_id', category.parent_id)
                await self._check_duplicate_name(
                    user_id, update_fields['name'], parent_id, exclude_id=category_id
                )
            
            # Validate other fields
            if 'name' in update_fields:
                self._validate_category_name(update_fields['name'])
            if 'color' in update_fields and update_fields['color']:
                self._validate_category_color(update_fields['color'])

            # Apply updates
            for field, value in update_fields.items():
                setattr(category, field, value)
            
            updated_category = await self.category_repo.update(category)
            logger.info(f"Category updated successfully: {category_id} for user {user_id}")
            return updated_category
            
        except (
            CategoryNotFoundError, CategoryValidationError, CategoryAlreadyExistsError,
            InvalidCategoryParentError, CategoryTypeConflictError, CircularCategoryReferenceError,
            DefaultCategoryModificationError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating category {category_id}: {str(e)}", exc_info=True)
            raise CategoryUpdateError(
                detail="Failed to update category due to internal error",
                context={"category_id": str(category_id), "user_id": user_id, "original_error": str(e)}
            )

    async def delete_category(
        self, 
        category_id: UUID, 
        user_id: str, 
        cascade: bool = False
    ) -> None:
        """Soft delete category with comprehensive business rule validation."""
        try:
            category = await self._get_category_or_raise(category_id, user_id)
            
            # Check if it's a default category
            if category.is_default:
                raise DefaultCategoryModificationError(
                    detail="Cannot delete default system category",
                    context={"category_id": str(category_id), "is_default": True}
                )
            
            # Check if category is in use (has expenses)
            if await self.category_repo.is_category_in_use(category_id):
                raise CategoryInUseError(
                    detail="Cannot delete category that has associated expenses",
                    context={"category_id": str(category_id)}
                )
            
            # Handle children validation
            active_children = await self.category_repo.get_children(category_id, user_id, include_inactive=False)
            
            if active_children and not cascade:
                raise CategoryHasChildrenError(
                    detail="Cannot delete category with active children. Use cascade=True or move children first",
                    context={
                        "category_id": str(category_id),
                        "children_count": len(active_children),
                        "cascade": cascade
                    }
                )
            
            # Handle cascade deletion
            if cascade and active_children:
                # Recursively validate and delete children
                for child in active_children:
                    await self.delete_category(child.id, user_id, cascade=True)
            
            # Perform soft delete
            await self.category_repo.delete(category)
            logger.info(f"Category deleted successfully: {category_id} for user {user_id}")
            
        except (
            CategoryNotFoundError, DefaultCategoryModificationError, 
            CategoryInUseError, CategoryHasChildrenError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting category {category_id}: {str(e)}", exc_info=True)
            raise CategoryDeleteError(
                detail="Failed to delete category due to internal error",
                context={"category_id": str(category_id), "user_id": user_id, "original_error": str(e)}
            )

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
        """Get categories with filtering and pagination."""
        try:
            # Validate pagination parameters
            if skip < 0:
                raise ValidationError(
                    detail="Skip parameter cannot be negative",
                    context={"skip": skip}
                )
            if limit <= 0 or limit > 1000:
                raise ValidationError(
                    detail="Limit must be between 1 and 1000",
                    context={"limit": limit}
                )
            
            return await self.category_repo.get_categories(
                user_id, skip, limit, category_type, parent_id, search, include_inactive
            )
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting categories for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve categories",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_category_by_id(self, category_id: UUID, user_id: str) -> Category:
        """Get category by ID - raises exception if not found."""
        return await self._get_category_or_raise(category_id, user_id)

    async def get_children(
        self, 
        category_id: UUID, 
        user_id: str, 
        include_inactive: bool = False
    ) -> List[Category]:
        """Get direct children of a category."""
        try:
            # Ensure parent category exists
            await self._get_category_or_raise(category_id, user_id)
            
            return await self.category_repo.get_children(category_id, user_id, include_inactive)
        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting children for category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to get category children",
                context={"category_id": str(category_id), "user_id": user_id, "original_error": str(e)}
            )

    async def get_category_stats(self, user_id: str) -> CategoryStatsResponse:
        """Get category statistics for the user."""
        try:
            return await self.category_repo.get_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting category stats for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve category statistics",
                context={"user_id": user_id, "original_error": str(e)}
            )

    # Private helper methods for validation

    async def _get_category_or_raise(self, category_id: UUID, user_id: str) -> Category:
        """Get category or raise CategoryNotFoundError."""
        try:
            category = await self.category_repo.get_by_id(category_id, user_id)
            if not category:
                raise CategoryNotFoundError(
                    detail=f"Category with ID {category_id} not found",
                    context={"category_id": str(category_id), "user_id": user_id}
                )
            return category
        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve category",
                context={"category_id": str(category_id), "user_id": user_id, "original_error": str(e)}
            )

    async def _validate_category_data(self, category_data: CategoryCreate, user_id: str) -> None:
        """Validate basic category data."""
        self._validate_category_name(category_data.name)
        
        if category_data.color:
            self._validate_category_color(category_data.color)

    def _validate_category_name(self, name: str) -> None:
        """Validate category name."""
        if not name or not name.strip():
            raise CategoryValidationError(
                detail="Category name cannot be empty",
                context={"name": name}
            )
        
        if len(name.strip()) > MAX_CATEGORY_NAME_LENGTH:
            raise CategoryNameTooLongError(
                detail=f"Category name must be {MAX_CATEGORY_NAME_LENGTH} characters or less",
                context={"name": name, "length": len(name), "max_length": MAX_CATEGORY_NAME_LENGTH}
            )

    def _validate_category_color(self, color: str) -> None:
        """Validate category color format."""
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise InvalidCategoryColorError(
                detail="Color must be in hex format (#RRGGBB)",
                context={"color": color}
            )

    async def _validate_parent_category(self, parent_id: UUID, user_id: str, child_type: CategoryType) -> Category:
        """Validate parent category exists and is compatible."""
        parent_category = await self._get_category_or_raise(parent_id, user_id)
        
        if parent_category.type != child_type:
            raise CategoryTypeConflictError(
                detail=f"Parent category type ({parent_category.type}) must match child type ({child_type})",
                context={
                    "parent_id": str(parent_id),
                    "parent_type": parent_category.type,
                    "child_type": child_type
                }
            )
        
        return parent_category

    async def _validate_hierarchy_depth(self, parent_id: UUID, user_id: str) -> None:
        """Validate that adding a child won't exceed depth limit."""
        try:
            current_depth = await self.category_repo.get_category_depth(parent_id, user_id)
            if current_depth >= MAX_CATEGORY_DEPTH:
                raise CategoryDepthLimitExceededError(
                    detail=f"Category hierarchy cannot exceed {MAX_CATEGORY_DEPTH} levels",
                    context={
                        "parent_id": str(parent_id),
                        "current_depth": current_depth,
                        "max_depth": MAX_CATEGORY_DEPTH
                    }
                )
        except Exception as e:
            logger.error(f"Error checking hierarchy depth: {str(e)}")
            raise InternalServerError(
                detail="Failed to validate hierarchy depth",
                context={"parent_id": str(parent_id), "original_error": str(e)}
            )

    async def _check_duplicate_name(
        self, 
        user_id: str, 
        name: str, 
        parent_id: Optional[UUID], 
        exclude_id: Optional[UUID] = None
    ) -> None:
        """Check for duplicate category name at the same level."""
        try:
            is_duplicate = await self.category_repo.check_duplicate_name(
                user_id, name, parent_id, exclude_id
            )
            
            if is_duplicate:
                raise CategoryAlreadyExistsError(
                    detail=f"Category '{name}' already exists at this level",
                    context={
                        "name": name,
                        "parent_id": str(parent_id) if parent_id else None,
                        "user_id": user_id
                    }
                )
        except CategoryAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Error checking duplicate name: {str(e)}")
            raise InternalServerError(
                detail="Failed to validate category name uniqueness",
                context={"name": name, "original_error": str(e)}
            )

    async def _validate_parent_change(self, category: Category, new_parent_id: Optional[UUID], user_id: str) -> None:
        """Validate parent change operation."""
        if new_parent_id == category.id:
            raise CircularCategoryReferenceError(
                detail="Category cannot be its own parent",
                context={"category_id": str(category.id)}
            )
        
        if new_parent_id:
            # Validate new parent exists and is compatible
            await self._validate_parent_category(new_parent_id, user_id, category.type)
            
            # Check for circular reference
            if await self.category_repo.check_circular_reference(category.id, new_parent_id, user_id):
                raise CircularCategoryReferenceError(
                    detail="This change would create a circular reference",
                    context={
                        "category_id": str(category.id),
                        "new_parent_id": str(new_parent_id)
                    }
                )
