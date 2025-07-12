from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import Optional, List, Tuple
from uuid import UUID
import math

from src.categories.models import Category, CategoryType
from src.categories.schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryHierarchy,
    CategoryPath, CategoryStatsResponse, CategoryWithChildren
)
from src.database import get_db
from src.exceptions import (
    CategoryNotFoundError, DuplicateCategoryError, InvalidCategoryParentError,
    CategoryTypeConflictError, CircularCategoryReferenceError
)


class CategoryService:
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def create_category(self, user_id: str, category_data: CategoryCreate) -> Category:
        """Create a new category with validation"""
        # Validate parent if provided
        parent_category = None
        if category_data.parent_id:
            parent_category = await self._get_category_by_id(category_data.parent_id, user_id)
            if not parent_category:
                raise InvalidCategoryParentError("Parent category not found")
            
            # Ensure parent and child have same type
            if parent_category.type != category_data.type:
                raise CategoryTypeConflictError(
                    f"Parent category type ({parent_category.type}) must match child type ({category_data.type})"
                )

        # Check for duplicate name at the same level
        existing_category = self.db.query(Category).filter(
            and_(
                Category.user_id == user_id,
                Category.name == category_data.name,
                Category.parent_id == category_data.parent_id,
                Category.is_active == True
            )
        ).first()
        
        if existing_category:
            raise DuplicateCategoryError(
                f"Category '{category_data.name}' already exists at this level"
            )

        # Create new category
        category = Category(
            user_id=user_id,
            **category_data.model_dump()
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        
        return category

    async def get_category_hierarchy(
        self, 
        user_id: str, 
        category_type: Optional[CategoryType] = None,
        include_inactive: bool = False
    ) -> List[CategoryHierarchy]:
        """Build hierarchical tree structure from root categories"""
        # Get all categories for the user
        query = self.db.query(Category).filter(Category.user_id == user_id)
        
        if category_type:
            query = query.filter(Category.type == category_type)
        
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        
        categories = query.options(joinedload(Category.children)).all()
        
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

    async def get_category_path(self, category_id: UUID, user_id: str) -> CategoryPath:
        """Generate breadcrumb path from root to category"""
        category = await self._get_category_by_id(category_id, user_id)
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
                current = await self._get_category_by_id(current.parent_id, user_id)
            else:
                current = None
        
        return CategoryPath(
            category_id=category_id,
            path=path,
            path_names=path_names
        )

    async def update_category(
        self, 
        category_id: UUID, 
        user_id: str, 
        category_data: CategoryUpdate
    ) -> Category:
        """Update category with validation"""
        category = await self._get_category_by_id(category_id, user_id)
        if not category:
            raise CategoryNotFoundError("Category not found")
        
        # Handle parent change validation
        if category_data.parent_id is not None:
            if category_data.parent_id == category.id:
                raise CircularCategoryReferenceError("Category cannot be its own parent")
            
            if category_data.parent_id:
                # Check if new parent exists
                new_parent = await self._get_category_by_id(category_data.parent_id, user_id)
                if not new_parent:
                    raise InvalidCategoryParentError("New parent category not found")
                
                # Check for circular reference
                if await self._would_create_circular_reference(category.id, category_data.parent_id):
                    raise CircularCategoryReferenceError("This change would create a circular reference")
                
                # Ensure type compatibility
                category_type = category_data.type or category.type
                if new_parent.type != category_type:
                    raise CategoryTypeConflictError("Parent and child categories must have the same type")

        # Check for duplicate name if name is being changed
        if category_data.name and category_data.name != category.name:
            parent_id = category_data.parent_id if category_data.parent_id is not None else category.parent_id
            existing_category = self.db.query(Category).filter(
                and_(
                    Category.user_id == user_id,
                    Category.name == category_data.name,
                    Category.parent_id == parent_id,
                    Category.id != category_id,
                    Category.is_active == True
                )
            ).first()
            
            if existing_category:
                raise DuplicateCategoryError(
                    f"Category '{category_data.name}' already exists at this level"
                )

        # Update fields
        for field, value in category_data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        
        self.db.commit()
        self.db.refresh(category)
        
        return category

    async def delete_category(
        self, 
        category_id: UUID, 
        user_id: str, 
        cascade: bool = False
    ) -> None:
        """Soft delete category with optional cascade for children"""
        category = await self._get_category_by_id(category_id, user_id)
        if not category:
            raise CategoryNotFoundError("Category not found")
        
        if cascade:
            # Recursively soft delete all descendants
            descendants = category.get_descendants()
            for descendant in descendants:
                descendant.is_active = False
        else:
            # Check if category has active children
            active_children = self.db.query(Category).filter(
                and_(
                    Category.parent_id == category_id,
                    Category.is_active == True
                )
            ).count()
            
            if active_children > 0:
                raise InvalidCategoryParentError(
                    "Cannot delete category with active children. Use cascade=True or move children first."
                )
        
        # Soft delete the category
        category.is_active = False
        self.db.commit()

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
        query = self.db.query(Category).filter(Category.user_id == user_id)
        
        # Apply filters
        if category_type:
            query = query.filter(Category.type == category_type)
        
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        
        if search:
            query = query.filter(Category.name.ilike(f"%{search}%"))
        
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        categories = query.order_by(Category.name).offset(skip).limit(limit).all()
        
        return categories, total

    async def get_category_by_id(self, category_id: UUID, user_id: str) -> Optional[Category]:
        """Get category by ID for the user"""
        return await self._get_category_by_id(category_id, user_id)

    async def get_children(
        self, 
        category_id: UUID, 
        user_id: str, 
        include_inactive: bool = False
    ) -> List[Category]:
        """Get direct children of a category"""
        query = self.db.query(Category).filter(
            and_(
                Category.user_id == user_id,
                Category.parent_id == category_id
            )
        )
        
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        
        return query.order_by(Category.name).all()

    async def get_category_stats(self, user_id: str) -> CategoryStatsResponse:
        """Get category statistics for the user"""
        # Basic counts
        total_categories = self.db.query(Category).filter(
            and_(Category.user_id == user_id, Category.is_active == True)
        ).count()
        
        expense_categories = self.db.query(Category).filter(
            and_(
                Category.user_id == user_id,
                Category.type == CategoryType.EXPENSE,
                Category.is_active == True
            )
        ).count()
        
        income_categories = self.db.query(Category).filter(
            and_(
                Category.user_id == user_id,
                Category.type == CategoryType.INCOME,
                Category.is_active == True
            )
        ).count()
        
        root_categories = self.db.query(Category).filter(
            and_(
                Category.user_id == user_id,
                Category.parent_id.is_(None),
                Category.is_active == True
            )
        ).count()
        
        # Categories by type
        type_counts = dict(
            self.db.query(Category.type, func.count(Category.id))
            .filter(and_(Category.user_id == user_id, Category.is_active == True))
            .group_by(Category.type)
            .all()
        )
        categories_by_type = {t: type_counts.get(t, 0) for t in CategoryType}
        
        # Calculate maximum depth
        max_depth = 0
        all_categories = self.db.query(Category).filter(
            and_(Category.user_id == user_id, Category.is_active == True)
        ).all()
        
        for category in all_categories:
            depth = category.get_level()
            max_depth = max(max_depth, depth)
        
        return CategoryStatsResponse(
            total_categories=total_categories,
            expense_categories=expense_categories,
            income_categories=income_categories,
            root_categories=root_categories,
            categories_by_type=categories_by_type,
            max_depth=max_depth
        )

    # Private helper methods
    async def _get_category_by_id(self, category_id: UUID, user_id: str) -> Optional[Category]:
        """Get category by ID ensuring it belongs to the user"""
        return self.db.query(Category).filter(
            and_(
                Category.id == category_id,
                Category.user_id == user_id,
                Category.is_active == True
            )
        ).first()

    async def _would_create_circular_reference(
        self, 
        category_id: UUID, 
        new_parent_id: UUID
    ) -> bool:
        """Check if setting new_parent_id would create a circular reference"""
        current_id = new_parent_id
        visited = set()
        
        while current_id and current_id not in visited:
            if current_id == category_id:
                return True
            
            visited.add(current_id)
            parent = self.db.query(Category).filter(Category.id == current_id).first()
            current_id = parent.parent_id if parent else None
        
        return False
