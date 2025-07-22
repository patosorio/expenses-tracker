from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_, or_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from .models import Category, CategoryType
from .schemas import CategoryHierarchy, CategoryPath, CategoryStatsResponse, CategoryResponse
from .exceptions import CategoryNotFoundError
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class CategoryRepository:
    """Repository for category data access operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # Core CRUD Operations
    async def create(self, category: Category) -> Category:
        """Create category in database with proper error handling."""
        try:
            self.db.add(category)
            await self.db.commit()
            await self.db.refresh(category)
            logger.info(f"Created category {category.id} for user {category.user_id}")
            return category
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating category: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while creating category",
                context={"original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating category: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while creating category",
                context={"original_error": str(e)}
            )

    async def get_by_id(self, category_id: UUID, user_id: str) -> Optional[Category]:
        """Get category by ID with user validation and optimized loading."""
        try:
            result = await self.db.execute(
                select(Category)
                .options(selectinload(Category.children))
                .where(
                    and_(
                        Category.id == category_id, 
                        Category.user_id == user_id, 
                        Category.is_active == True
                    )
                )
            )
            category = result.scalar_one_or_none()
            
            if not category:
                logger.debug(f"Category {category_id} not found for user {user_id}")
                
            return category
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving category",
                context={"category_id": str(category_id), "original_error": str(e)}
            )

    async def update(self, category: Category) -> Category:
        """Update category in database with proper error handling."""
        try:
            await self.db.commit()
            await self.db.refresh(category)
            logger.info(f"Updated category {category.id} for user {category.user_id}")
            return category
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating category {category.id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while updating category",
                context={"category_id": str(category.id), "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error updating category {category.id}: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while updating category",
                context={"category_id": str(category.id), "original_error": str(e)}
            )

    async def delete(self, category: Category) -> bool:
        """Soft delete category with proper error handling."""
        try:
            category.is_active = False
            await self.db.commit()
            logger.info(f"Soft deleted category {category.id} for user {category.user_id}")
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error deleting category {category.id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while deleting category",
                context={"category_id": str(category.id), "original_error": str(e)}
            )

    # Query Operations
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
        # Build base query
        query = select(Category).where(Category.user_id == user_id)
        
        if not include_inactive:
            query = query.where(Category.is_active == True)
        
        if category_type:
            query = query.where(Category.type == category_type)
        
        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(Category.name.ilike(search_term))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()
        
        # Apply pagination
        query = (query
                    .order_by(Category.name)
                    .offset(skip)
                    .limit(limit))
                    
        result = await self.db.execute(query)
        categories = list(result.scalars().all())
        
        return categories, total_count

    async def get_children(
        self, 
        category_id: UUID, 
        user_id: str, 
        include_inactive: bool = False
    ) -> List[Category]:
        """Get direct children of a category."""
        try:
            query = select(Category).where(
                and_(
                    Category.parent_id == category_id, 
                    Category.user_id == user_id
                )
            ).order_by(Category.name)
            
            if not include_inactive:
                query = query.where(Category.is_active == True)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting children for category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving category children",
                context={"category_id": str(category_id), "original_error": str(e)}
            )

    async def get_hierarchy(
        self, 
        user_id: str, 
        category_type: Optional[CategoryType] = None,
        include_inactive: bool = False
    ) -> List[CategoryHierarchy]:
        """Build hierarchical tree structure from root categories - optimized."""
        try:
            # Get all categories for the user with eager loading
            query = (select(Category)
                    .options(selectinload(Category.children))
                    .where(Category.user_id == user_id))
            
            if category_type:
                query = query.where(Category.type == category_type)
            
            if not include_inactive:
                query = query.where(Category.is_active == True)
                
            query = query.order_by(Category.parent_id.nulls_first(), Category.name)
            
            result = await self.db.execute(query)
            categories = list(result.scalars().all())
            
            # Build category lookup for O(1) access
            category_map = {cat.id: cat for cat in categories}
            
            # Build hierarchy starting from root categories
            root_categories = [cat for cat in categories if cat.parent_id is None]
            
            def build_hierarchy(category: Category, level: int = 0) -> CategoryHierarchy:
                # Get ancestors path
                path = []
                current = category
                while current:
                    path.insert(0, current.name)
                    if current.parent_id and current.parent_id in category_map:
                        current = category_map[current.parent_id]
                    else:
                        break
                
                # Get children recursively
                children = []
                for child in categories:
                    if (child.parent_id == category.id and 
                        (child.is_active or include_inactive)):
                        children.append(build_hierarchy(child, level + 1))
                
                return CategoryHierarchy(
                    id=category.id,
                    name=category.name,
                    type=category.type,
                    color=category.color,
                    icon=category.icon,
                    level=level,
                    path=path,
                    children=children
                )
            
            return [build_hierarchy(cat) for cat in root_categories]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error building hierarchy for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while building category hierarchy",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_path(self, category_id: UUID, user_id: str) -> CategoryPath:
        """Generate breadcrumb path from root to category - optimized."""
        try:
            category = await self.get_by_id(category_id, user_id)
            if not category:
                from .exceptions import CategoryNotFoundError
                raise CategoryNotFoundError(
                    detail=f"Category {category_id} not found",
                    context={"category_id": str(category_id), "user_id": user_id}
                )
            
            path = []
            path_names = []
            current = category
            
            # Build path from current to root efficiently
            while current:
                path.insert(0, CategoryResponse.model_validate(current))
                path_names.insert(0, current.name)
                if current.parent_id:
                    current = await self.get_by_id(current.parent_id, user_id)
                else:
                    current = None
            
            return CategoryPath(
                category_id=category_id,
                path=path,
                path_names=path_names
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting path for category {category_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while getting category path",
                context={"category_id": str(category_id), "original_error": str(e)}
            )

    async def get_stats(self, user_id: str) -> CategoryStatsResponse:
        """Get category statistics with optimized queries."""
        try:
            # Single query to get all stats efficiently
            stats_query = await self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_categories,
                    COUNT(CASE WHEN type = 'EXPENSE' THEN 1 END) as expense_categories,
                    COUNT(CASE WHEN type = 'INCOME' THEN 1 END) as income_categories,
                    COUNT(CASE WHEN parent_id IS NULL THEN 1 END) as root_categories,
                    COUNT(DISTINCT parent_id) FILTER (WHERE parent_id IS NOT NULL) as categories_with_children,
                    AVG(COALESCE(level, 0)) as avg_depth
                FROM categories 
                WHERE user_id = :user_id AND is_active = true
            """), {"user_id": user_id})
            
            stats = stats_query.fetchone()
            
            return CategoryStatsResponse(
                total_categories=stats.total_categories or 0,
                expense_categories=stats.expense_categories or 0,
                income_categories=stats.income_categories or 0,
                categories_with_children=stats.categories_with_children or 0,
                root_categories=stats.root_categories or 0,
                average_depth=round(float(stats.avg_depth or 0), 2)
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting stats for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving category statistics",
                context={"user_id": user_id, "original_error": str(e)}
            )

    # Validation and Business Logic Support Methods

    async def check_duplicate_name(
        self,
        user_id: str,
        name: str,
        parent_id: Optional[UUID] = None,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if category name already exists at the same level."""
        try:
            query = select(Category).where(
                and_(
                    Category.user_id == user_id,
                    func.lower(Category.name) == func.lower(name.strip()),
                    Category.parent_id == parent_id,
                    Category.is_active == True
                )
            )
            
            if exclude_id:
                query = query.where(Category.id != exclude_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking duplicate name: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking duplicate category name",
                context={"name": name, "original_error": str(e)}
            )

    async def check_circular_reference(
        self,
        category_id: UUID,
        new_parent_id: UUID,
        user_id: str
    ) -> bool:
        """Check if setting new_parent_id would create a circular reference."""
        try:
            if category_id == new_parent_id:
                return True
            
            # Use recursive CTE to check ancestry efficiently
            ancestry_query = await self.db.execute(text("""
                WITH RECURSIVE category_ancestry AS (
                    SELECT id, parent_id, 1 as level
                    FROM categories 
                    WHERE id = :new_parent_id AND user_id = :user_id AND is_active = true
                    
                    UNION ALL
                    
                    SELECT c.id, c.parent_id, ca.level + 1
                    FROM categories c
                    INNER JOIN category_ancestry ca ON c.id = ca.parent_id
                    WHERE c.user_id = :user_id AND c.is_active = true AND ca.level < 10
                )
                SELECT 1 FROM category_ancestry WHERE id = :category_id LIMIT 1
            """), {
                "category_id": str(category_id),
                "new_parent_id": str(new_parent_id),
                "user_id": user_id
            })
            
            return ancestry_query.fetchone() is not None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking circular reference: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking circular reference",
                context={"category_id": str(category_id), "new_parent_id": str(new_parent_id), "original_error": str(e)}
            )

    async def get_category_depth(self, category_id: UUID, user_id: str) -> int:
        """Get the depth of a category in the hierarchy."""
        try:
            depth_query = await self.db.execute(text("""
                WITH RECURSIVE category_depth AS (
                    SELECT id, parent_id, 0 as depth
                    FROM categories 
                    WHERE id = :category_id AND user_id = :user_id AND is_active = true
                    
                    UNION ALL
                    
                    SELECT c.id, c.parent_id, cd.depth + 1
                    FROM categories c
                    INNER JOIN category_depth cd ON c.parent_id = cd.id
                    WHERE c.user_id = :user_id AND c.is_active = true AND cd.depth < 10
                )
                SELECT MAX(depth) FROM category_depth
            """), {"category_id": str(category_id), "user_id": user_id})
            
            result = depth_query.scalar()
            return result or 0
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting category depth: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while calculating category depth",
                context={"category_id": str(category_id), "original_error": str(e)}
            )

    async def is_category_in_use(self, category_id: UUID) -> bool:
        """Check if category is being used by any expenses."""
        try:
            # Check if category has any expenses
            usage_query = await self.db.execute(text("""
                SELECT 1 FROM expenses 
                WHERE category_id = :category_id AND is_active = true 
                LIMIT 1
            """), {"category_id": str(category_id)})
            
            return usage_query.fetchone() is not None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking category usage: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking category usage",
                context={"category_id": str(category_id), "original_error": str(e)}
            )
