from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from .models import Category, CategoryType
from .schemas import CategoryHierarchy, CategoryPath, CategoryStatsResponse, CategoryResponse
from .exceptions import CategoryNotFoundError

logger = logging.getLogger(__name__)


class CategoryRepository:
    """Repository for category data access operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # Core CRUD Operations
    async def create(self, category: Category) -> Category:
        """Create category in database"""
        try:
            self.db.add(category)
            await self.db.commit()
            await self.db.refresh(category)
            logger.info(f"Created category {category.id} for user {category.user_id}")
            return category
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating category: {str(e)}")
            raise

    async def get_by_id(self, category_id: UUID, user_id: str) -> Optional[Category]:
        """Get category by ID with user validation"""
        result = await self.db.execute(
            select(Category).where(
                and_(Category.id == category_id, Category.user_id == user_id, Category.is_active == True)
            )
        )
        category = result.scalar_one_or_none()
        
        if not category:
            logger.warning(f"Category {category_id} not found for user {user_id}")
            return None
            
        return category

    async def update(self, category: Category) -> Category:
        """Update category in database"""
        try:
            await self.db.commit()
            await self.db.refresh(category)
            logger.info(f"Updated category {category.id} for user {category.user_id}")
            return category
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating category {category.id}: {str(e)}")
            raise

    async def delete(self, category: Category) -> bool:
        """Soft delete category"""
        try:
            category.is_active = False
            await self.db.commit()
            logger.info(f"Soft deleted category {category.id} for user {category.user_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting category {category.id}: {str(e)}")
            raise

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
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        return categories, total_count

    async def get_children(
        self, 
        category_id: UUID, 
        user_id: str, 
        include_inactive: bool = False
    ) -> List[Category]:
        """Get direct children of a category"""
        query = select(Category).where(
            and_(Category.parent_id == category_id, Category.user_id == user_id)
        )
        
        if not include_inactive:
            query = query.where(Category.is_active == True)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_hierarchy(
        self, 
        user_id: str, 
        category_type: Optional[CategoryType] = None,
        include_inactive: bool = False
    ) -> List[CategoryHierarchy]:
        """Build hierarchical tree structure from root categories"""
        # Get all categories for the user
        query = select(Category).where(Category.user_id == user_id)
        
        if category_type:
            query = query.where(Category.type == category_type)
        
        if not include_inactive:
            query = query.where(Category.is_active == True)
        
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        # Build category lookup
        category_map = {cat.id: cat for cat in categories}
        
        # Build hierarchy starting from root categories
        root_categories = [cat for cat in categories if cat.parent_id is None]
        
        def build_hierarchy(category: Category, level: int = 0) -> CategoryHierarchy:
            # Get ancestors path
            path = []
            current = category
            while current.parent_id and current.parent_id in category_map:
                current = category_map[current.parent_id]
                path.insert(0, current.name)
            path.append(category.name)
            
            # Get children
            children = []
            for child in category.children:
                if child.is_active or include_inactive:
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

    async def get_path(self, category_id: UUID, user_id: str) -> CategoryPath:
        """Generate breadcrumb path from root to category"""
        category = await self.get_by_id(category_id, user_id)
        if not category:
            raise CategoryNotFoundError("Category not found")
        
        path = []
        path_names = []
        current = category
        
        # Build path from current to root
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

    async def get_stats(self, user_id: str) -> CategoryStatsResponse:
        """Get category statistics"""
        # Total categories by type
        total_expense_result = await self.db.execute(
            select(func.count(Category.id))
            .where(and_(Category.user_id == user_id, Category.type == CategoryType.EXPENSE, Category.is_active == True))
        )
        total_expense = total_expense_result.scalar()
        
        total_income_result = await self.db.execute(
            select(func.count(Category.id))
            .where(and_(Category.user_id == user_id, Category.type == CategoryType.INCOME, Category.is_active == True))
        )
        total_income = total_income_result.scalar()
        
        # Categories with children
        categories_with_children_result = await self.db.execute(
            select(func.count(Category.id))
            .where(and_(Category.user_id == user_id, Category.is_active == True))
            .join(Category.children)
        )
        categories_with_children = categories_with_children_result.scalar()
        
        # Root categories
        root_categories_result = await self.db.execute(
            select(func.count(Category.id))
            .where(and_(Category.user_id == user_id, Category.parent_id.is_(None), Category.is_active == True))
        )
        root_categories = root_categories_result.scalar()
        
        # Average depth
        depth_result = await self.db.execute(
            select(func.avg(func.coalesce(Category.level, 0)))
            .where(and_(Category.user_id == user_id, Category.is_active == True))
        )
        avg_depth = depth_result.scalar() or 0
        
        return CategoryStatsResponse(
            total_categories=total_expense + total_income,
            expense_categories=total_expense,
            income_categories=total_income,
            categories_with_children=categories_with_children or 0,
            root_categories=root_categories,
            average_depth=round(avg_depth, 2)
        )

    async def check_duplicate_name(
        self,
        user_id: str,
        name: str,
        parent_id: Optional[UUID] = None,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if category name already exists at the same level"""
        query = select(Category).where(
            and_(
                Category.user_id == user_id,
                Category.name == name,
                Category.parent_id == parent_id,
                Category.is_active == True
            )
        )
        
        if exclude_id:
            query = query.where(Category.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def check_circular_reference(
        self,
        category_id: UUID,
        new_parent_id: UUID,
        user_id: str
    ) -> bool:
        """Check if setting new_parent_id would create a circular reference"""
        if category_id == new_parent_id:
            return True
        
        # Check if new_parent_id is a descendant of category_id
        current = new_parent_id
        while current:
            parent = await self.get_by_id(current, user_id)
            if not parent:
                break
            if parent.parent_id == category_id:
                return True
            current = parent.parent_id
        
        return False 