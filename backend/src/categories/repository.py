from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, select
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from .models import Category, CategoryType
from .schemas import CategoryHierarchy, CategoryPath, CategoryStatsResponse
from ..core.shared.base_repository import BaseRepository
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class CategoryRepository(BaseRepository[Category]):
    """Repository for category data access
    operations extending BaseRepository."""
    
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Category)

   # Specialized Category Methods
    async def get_by_name(
        self, 
        user_id: str, 
        name: str, 
        parent_id: Optional[UUID] = None
    ) -> Optional[Category]:
        """Get category by name and parent (for uniqueness validation)."""
        try:
            query = self._build_base_query(user_id)
            query = query.where(
                and_(
                    func.lower(Category.name) == name.lower(),
                    Category.parent_id == parent_id
                )
            )
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Database error getting category by name: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking category name",
                context={"user_id": user_id, "name": name, "parent_id": str(parent_id)}
            )
        
    async def get_children(
        self, 
        parent_id: UUID, 
        user_id: str, 
        include_inactive: bool = False
    ) -> List[Category]:
        """Get direct children of a category."""
        try:
            query = self._build_base_query(user_id, include_inactive)
            query = query.where(Category.parent_id == parent_id)
            query = query.order_by(Category.name)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Database error getting category children: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving category children",
                context={"parent_id": str(parent_id), "user_id": user_id}
            )
        
    async def get_hierarchy(
        self, 
        user_id: str, 
        category_type: Optional[CategoryType] = None,
        include_inactive: bool = False
    ) -> List[CategoryHierarchy]:
        """Build hierarchical tree structure from root categories."""
        try:
            # Get all categories for user
            query = self._build_base_query(user_id, include_inactive)
            if category_type:
                query = query.where(Category.type == category_type)
            query = query.order_by(Category.name)
            
            result = await self.db.execute(query)
            all_categories = list(result.scalars().all())
            
            # Build hierarchy tree
            return self._build_category_tree(all_categories)
            
        except Exception as e:
            logger.error(f"Database error building category hierarchy: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while building category hierarchy",
                context={"user_id": user_id, "category_type": category_type}
            )
        
    async def get_category_path(self, category_id: UUID, user_id: str) -> CategoryPath:
        """Get breadcrumb path from root to category."""
        try:
            category = await self.get_by_id_or_raise(category_id, user_id)
            path_items = []
            current = category
            
            # Walk up the tree to build path
            while current:
                path_items.insert(0, {
                    "id": current.id,
                    "name": current.name,
                    "type": current.type
                })
                
                if current.parent_id:
                    current = await self.get_by_id(current.parent_id, user_id)
                else:
                    current = None
            
            return CategoryPath(path=path_items)
            
        except Exception as e:
            logger.error(f"Database error getting category path: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while building category path",
                context={"category_id": str(category_id), "user_id": user_id}
            )

    async def get_stats(self, user_id: str) -> CategoryStatsResponse:
        """Get category statistics for the user."""
        try:
            # Get category counts by type
            expense_count = await self.count(
                user_id=user_id, 
                filters={"type": CategoryType.EXPENSE}
            )
            
            income_count = await self.count(
                user_id=user_id,
                filters={"type": CategoryType.INCOME}
            )
            
            # Get root category count
            root_count = await self.count(
                user_id=user_id,
                filters={"parent_id": None}
            )
            
            return CategoryStatsResponse(
                total_categories=expense_count + income_count,
                expense_categories=expense_count,
                income_categories=income_count,
                root_categories=root_count
            )
            
        except Exception as e:
            logger.error(f"Database error getting category stats: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving category statistics",
                context={"user_id": user_id}
            )

    async def get_depth(self, category_id: UUID, user_id: str) -> int:
        """Calculate the depth of a category in the hierarchy."""
        try:
            category = await self.get_by_id_or_raise(category_id, user_id)
            depth = 0
            current = category
            
            while current and current.parent_id:
                depth += 1
                current = await self.get_by_id(current.parent_id, user_id)
                
                # Prevent infinite loops
                if depth > 10:  # Max reasonable depth
                    break
            
            return depth
            
        except Exception as e:
            logger.error(f"Database error calculating category depth: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while calculating category depth",
                context={"category_id": str(category_id), "user_id": user_id}
            )

    # Override base methods for category-specific behavior
    async def get_paginated(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_field: str = "name",  # Categories default sort by name
        sort_order: str = "asc",   # Categories default ascending
        filters: Optional[dict] = None
    ) -> Tuple[List[Category], int]:
        """Override to provide category-specific defaults and search fields."""
        if search_fields is None:
            search_fields = ["name"]
        
        return await super().get_paginated(
            user_id=user_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            search_fields=search_fields,
            sort_field=sort_field,
            sort_order=sort_order,
            filters=filters
        )

    # Helper methods
    def _build_category_tree(self, categories: List[Category]) -> List[CategoryHierarchy]:
        """Build hierarchical tree structure from flat list of categories."""
        # Create lookup dict
        category_dict = {cat.id: cat for cat in categories}
        tree = []
        
        # Find root categories and build tree
        for category in categories:
            if category.parent_id is None:
                tree.append(self._build_category_node(category, category_dict))
        
        return tree

    def _build_category_node(
        self, 
        category: Category, 
        category_dict: dict
    ) -> CategoryHierarchy:
        """Build a single node in the category tree."""
        # Find children
        children = [
            self._build_category_node(child, category_dict)
            for child in category_dict.values()
            if child.parent_id == category.id
        ]
        
        return CategoryHierarchy(
            id=category.id,
            name=category.name,
            type=category.type,
            color=category.color,
            icon=category.icon,
            is_default=category.is_default,
            is_active=category.is_active,
            created_at=category.created_at,
            children=sorted(children, key=lambda x: x.name)
        )
