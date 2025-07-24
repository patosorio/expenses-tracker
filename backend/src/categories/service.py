from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
import re
import logging

from .models import Category, CategoryType
from .repository import CategoryRepository
from .schemas import *
from .exceptions import *
from ..core.shared.base_service import BaseService
from ..core.shared.exceptions import ValidationError, InternalServerError

logger = logging.getLogger(__name__)

# Business constants
MAX_CATEGORY_DEPTH = 5
MAX_CATEGORY_NAME_LENGTH = 100


class CategoryService(BaseService[Category, CategoryRepository]):
    """Category service with business logic extending BaseService."""
    def __init__(self, db: AsyncSession):
        super().__init__(db, CategoryRepository, Category)

    async def create_category(
            self,
            user_id: str,
            category_data: CategoryCreate
    ) -> Category:
        """Create a new category with validation"""
        try:
            # Convert Pydantic model to dict for processing
            data = category_data.model_dump()
            
            # Pre-create validation
            await self._pre_create_validation(data, user_id)
            
            # Create category
            category = await self.create(data, user_id)
            
            # Post-create actions
            # TODO: await self._post_create_actions(category, user_id)
            
            logger.info(f"Category created successfully: {category.id} for user {user_id}")
            return category
            
        except (ValidationError, CategoryValidationError, CategoryAlreadyExistsError, 
                InvalidCategoryParentError, CategoryTypeConflictError, 
                CategoryDepthLimitExceededError):
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error creating category for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to create category due to internal error",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def update_category(
            self,
            category_id: UUID, 
            user_id: str, 
            category_data: CategoryUpdate
    ) -> Category:
        """Update category with validation."""
        try:
            # Get existing category
            category = await self.get_by_id_or_raise(category_id, user_id)
            
            # Convert update data to dict
            update_data = category_data.model_dump(exclude_unset=True)
            
            # Pre-update validation
            #TODO: await self._pre_update_validation(category, update_data, user_id)
            
            # Update category
            updated_category = await self.update(category_id, update_data, user_id)
            
            # Post-update actions
            # TODO: await self._post_update_actions(updated_category, user_id)
            
            logger.info(f"Category updated successfully: {category_id}")
            return updated_category
            
        except (ValidationError, CategoryValidationError, CategoryNotFoundError):
            raise

        except Exception as e:
            logger.error(f"Unexpected error updating category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to update category",
                context={"category_id": str(category_id), "user_id": user_id}
            )
        
    async def delete_category(
        self,
        category_id: UUID,
        user_id: str,
        cascade: bool = False
    ) -> None:
        """Delete category with optional cascade to children"""
        try: 
            category = await self.get_by_id_or_raise(category_id, user_id)

            # Pre-delete validation
            await self._pre_delete_validation(category, user_id)

            if cascade:
                await self._cascade_delete_children(category_id, user_id)
            else:
                # Check if category has children
                children = await self.repository.get_children(category_id, user_id)
                if children:
                    raise CategoryHasChildrenError(
                        detail="Cannot delete category with children. Use cascade=true to delete children.",
                        context={"category_id": str(category_id), "children_count": len(children)}
                    )
            
            # Soft delete category
            await self.delete(category_id, user_id, soft=True)

            # Post delete
            await self._post_delete_actions(category_id, user_id)

        except (CategoryNotFoundError, CategoryHasChildrenError, CategoryInUseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to delete category",
                context={"category_id": str(category_id), "user_id": user_id}
            )
        
    async def get_category_hierarchy(
        self, 
        user_id: str, 
        category_type: Optional[CategoryType] = None,
        include_inactive: bool = False
    ) -> List[CategoryHierarchy]:
        """Build hierarchical tree structure from root categories."""
        try:
            return await self.repository.get_hierarchy(user_id, category_type, include_inactive)
        except Exception as e:
            logger.error(f"Error getting category hierarchy for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve category hierarchy",
                context={"user_id": user_id, "category_type": category_type}
            )
    
    async def get_category_path(self, category_id: UUID, user_id: str) -> CategoryPath:
        """Get category breadcrumb path from root to category."""
        try:
            # Validate category exists and belongs to user
            await self.get_by_id_or_raise(category_id, user_id)
            return await self.repository.get_category_path(category_id, user_id)
        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting category path: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve category path",
                context={"category_id": str(category_id), "user_id": user_id}
            )

    async def get_children(
        self, 
        category_id: UUID, 
        user_id: str, 
        include_inactive: bool = False
    ) -> List[Category]:
        """Get direct children of a category."""
        try:
            # Validate parent category exists
            await self.get_by_id_or_raise(category_id, user_id)
            return await self.repository.get_children(category_id, user_id, include_inactive)
        except CategoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting children for category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to get category children",
                context={"category_id": str(category_id), "user_id": user_id}
            )

    async def get_category_stats(self, user_id: str) -> CategoryStatsResponse:
        """Get category statistics for the user."""
        try:
            return await self.repository.get_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting category stats for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve category statistics",
                context={"user_id": user_id}
            )

    # Override BaseService methods for category-specific behavior
    async def get_paginated(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: Optional[str] = None,
        sort_field: str = "name",
        sort_order: str = "asc",
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Category], int]:
        """Get categories with pagination - override for category-specific defaults."""
        return await super().get_paginated(
            user_id=user_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            search_fields=["name"],  # Category-specific search fields
            sort_field=sort_field,
            sort_order=sort_order,
            filters=filters
        )

    # Override BaseService validation hooks
    async def _pre_create_validation(self, entity_data: Dict[str, Any], user_id: str) -> None:
        """Category-specific pre-create validation."""
        await self._validate_category_data(entity_data, user_id)
        
        # Validate parent if provided
        if entity_data.get('parent_id'):
            await self._validate_parent_category(
                entity_data['parent_id'], 
                user_id, 
                entity_data['type']
            )
            await self._validate_hierarchy_depth(entity_data['parent_id'], user_id)

        # Check for duplicate name at the same level
        await self._check_duplicate_name(
            user_id,
            entity_data['name'],
            entity_data.get('parent_id')
        )

    async def _pre_update_validation(
        self, 
        entity: Category, 
        update_data: Dict[str, Any], 
        user_id: str
    ) -> None:
        """Category-specific pre-update validation."""
        # Validate update data
        if update_data:
            await self._validate_category_data(update_data, user_id, is_update=True)
        
        # Check name uniqueness if name is being updated
        if 'name' in update_data:
            await self._check_duplicate_name(
                user_id,
                update_data['name'],
                update_data.get('parent_id', entity.parent_id),
                exclude_id=entity.id
            )
        
        # Validate parent change if parent_id is being updated
        if 'parent_id' in update_data and update_data['parent_id'] != entity.parent_id:
            if update_data['parent_id']:
                await self._validate_parent_category(
                    update_data['parent_id'], 
                    user_id, 
                    update_data.get('type', entity.type)
                )
                await self._validate_hierarchy_depth(update_data['parent_id'], user_id)
                
                # Prevent circular references
                await self._validate_no_circular_reference(entity.id, update_data['parent_id'], user_id)

    async def _pre_delete_validation(self, entity: Category, user_id: str) -> None:
        """Category-specific pre-delete validation."""
        # Check if category is in use by expenses (if expense model exists)
        # This would require checking with expense service
        # TODO
        pass

    # Category-specific validation methods
    async def _validate_category_data(
        self, 
        data: Dict[str, Any], 
        user_id: str,
        is_update: bool = False
    ) -> None:
        """Validate category data fields."""
        if not is_update:
            # Required fields for creation
            self._validate_required_fields(data, ['name', 'type'])
        
        # Validate field lengths
        self._validate_field_length(data, {
            'name': MAX_CATEGORY_NAME_LENGTH,
            'color': 7,  # Hex color format
            'icon': 10   # Emoji length
        })
        
        # Validate enum values
        self._validate_enum_values(data, {
            'type': [CategoryType.EXPENSE.value, CategoryType.INCOME.value]
        })
        
        # Validate color format if provided
        if 'color' in data and data['color']:
            if not re.match(r"^#[0-9A-Fa-f]{6}, data['color']"):
                raise CategoryValidationError(
                    detail="Color must be in hex format (#RRGGBB)",
                    context={"color": data['color']}
                )

    async def _validate_parent_category(
        self, 
        parent_id: UUID, 
        user_id: str, 
        category_type: CategoryType
    ) -> Category:
        """Validate parent category exists and type matches."""
        parent_category = await self.get_by_id(parent_id, user_id)
        
        if not parent_category:
            raise InvalidCategoryParentError(
                detail="Parent category not found",
                context={"parent_id": str(parent_id)}
            )
        
        if parent_category.type != category_type:
            raise CategoryTypeConflictError(
                detail=f"Parent category type ({parent_category.type}) must match child type ({category_type})",
                context={
                    "parent_id": str(parent_id),
                    "parent_type": parent_category.type,
                    "child_type": category_type
                }
            )
        
        return parent_category

    async def _validate_hierarchy_depth(self, parent_id: UUID, user_id: str) -> None:
        """Validate hierarchy doesn't exceed maximum depth."""
        depth = await self.repository.get_depth(parent_id, user_id)
        
        if depth >= MAX_CATEGORY_DEPTH:
            raise CategoryDepthLimitExceededError(
                detail=f"Category hierarchy cannot exceed {MAX_CATEGORY_DEPTH} levels",
                context={"current_depth": depth, "max_depth": MAX_CATEGORY_DEPTH}
            )

    async def _check_duplicate_name(
        self, 
        user_id: str, 
        name: str, 
        parent_id: Optional[UUID],
        exclude_id: Optional[UUID] = None
    ) -> None:
        """Check for duplicate category names at the same level."""
        existing = await self.repository.get_by_name(user_id, name, parent_id)
        
        if existing and (exclude_id is None or existing.id != exclude_id):
            raise CategoryAlreadyExistsError(
                detail="Category with this name already exists at this level",
                context={
                    "name": name,
                    "parent_id": str(parent_id) if parent_id else None,
                    "existing_id": str(existing.id)
                }
            )

    async def _validate_no_circular_reference(
        self, 
        category_id: UUID, 
        new_parent_id: UUID, 
        user_id: str
    ) -> None:
        """Validate that setting new parent doesn't create circular reference."""
        current_id = new_parent_id
        visited = set()
        
        while current_id and current_id not in visited:
            if current_id == category_id:
                raise CategoryValidationError(
                    detail="Cannot set parent: would create circular reference",
                    context={"category_id": str(category_id), "parent_id": str(new_parent_id)}
                )
            
            visited.add(current_id)
            parent = await self.get_by_id(current_id, user_id)
            current_id = parent.parent_id if parent else None

    async def _cascade_delete_children(self, parent_id: UUID, user_id: str) -> None:
        """Recursively soft delete all children of a category."""
        children = await self.repository.get_children(parent_id, user_id, include_inactive=True)
        
        for child in children:
            # Recursively delete grandchildren first
            await self._cascade_delete_children(child.id, user_id)
            
            # Then delete the child
            await self.delete(child.id, user_id, soft=True)
