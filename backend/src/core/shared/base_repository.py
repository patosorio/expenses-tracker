# backend/src/core/shared/base_repository.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload, DeclarativeBase
from typing import TypeVar, Generic, Type, Any
from collections.abc import Sequence
from uuid import UUID
import logging

from .exceptions import InternalServerError, NotFoundError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=DeclarativeBase)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations and patterns."""
    
    def __init__(self, db: AsyncSession, model_class: Type[T]) -> None:
        self.db = db
        self.model_class = model_class
        self.model_name = model_class.__name__.lower()

    # Core CRUD Operations
    async def create(self, entity: T) -> T:
        """Create entity in database with proper error handling."""
        try:
            self.db.add(entity)
            await self.db.commit()
            await self.db.refresh(entity)
            logger.info(f"Created {self.model_name} {getattr(entity, 'id', 'unknown')}")
            return entity
        
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while creating {self.model_name}",
                context={"original_error": str(e)}
            )
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Unexpected error occurred while creating {self.model_name}",
                context={"original_error": str(e)}
            )

    async def get_by_id(
        self, 
        entity_id: UUID, 
        user_id: str | None = None,
        include_inactive: bool = False
    ) -> T | None:
        """Get entity by ID with optional user validation."""
        try:
            query = select(self.model_class).where(self.model_class.id == entity_id)
            
            # Add user isolation if user_id provided and model supports it
            if user_id and hasattr(self.model_class, 'user_id'):
                query = query.where(self.model_class.user_id == user_id)
            
            # Filter out inactive records unless requested
            if not include_inactive and hasattr(self.model_class, 'is_active'):
                query = query.where(self.model_class.is_active.is_(True))
            
            result = await self.db.execute(query)
            entity = result.scalar_one_or_none()
            
            if not entity:
                logger.debug(f"{self.model_name.title()} {entity_id} not found")
            
            return entity
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while retrieving {self.model_name}",
                context={"entity_id": str(entity_id), "original_error": str(e)}
            )

    async def get_by_id_or_raise(
        self, 
        entity_id: UUID, 
        user_id: str | None = None,
        include_inactive: bool = False
    ) -> T:
        """Get entity by ID or raise NotFoundError."""
        entity = await self.get_by_id(entity_id, user_id, include_inactive)
        if not entity:
            raise NotFoundError(
                detail=f"{self.model_name.title()} not found",
                context={"entity_id": str(entity_id)}
            )
        return entity

    async def update(self, entity: T, update_data: dict[str, Any]) -> T:
        """Update entity with provided data."""
        try:
            for field, value in update_data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)
            
            await self.db.commit()
            await self.db.refresh(entity)
            logger.info(f"Updated {self.model_name} {getattr(entity, 'id', 'unknown')}")
            return entity
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while updating {self.model_name}",
                context={"entity_id": str(getattr(entity, 'id', 'unknown')), "original_error": str(e)}
            )

    async def soft_delete(self, entity: T) -> T:
        """Soft delete entity (set is_active = False)."""
        if not hasattr(entity, 'is_active'):
            msg = f"{self.model_name} does not support soft deletion"
            raise ValueError(msg)
        
        return await self.update(entity, {"is_active": False})

    async def hard_delete(self, entity: T) -> None:
        """Hard delete entity from database."""
        try:
            await self.db.delete(entity)
            await self.db.commit()
            logger.info(f"Hard deleted {self.model_name} {getattr(entity, 'id', 'unknown')}")
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error deleting {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while deleting {self.model_name}",
                context={"entity_id": str(getattr(entity, 'id', 'unknown')), "original_error": str(e)}
            )

    # Query Building Helpers
    def _build_base_query(self, user_id: str | None = None, include_inactive: bool = False):
        """Build base query with common filters."""
        query = select(self.model_class)
        
        # Add user isolation
        if user_id and hasattr(self.model_class, 'user_id'):
            query = query.where(self.model_class.user_id == user_id)
        
        # Filter active records
        if not include_inactive and hasattr(self.model_class, 'is_active'):
            query = query.where(self.model_class.is_active.is_(True))
        
        return query

    def _apply_search(self, query, search_term: str, search_fields: list[str]):
        """Apply search across multiple fields."""
        if not search_term or not search_fields:
            return query
        
        search_conditions = []
        search_pattern = f"%{search_term.lower()}%"
        
        for field in search_fields:
            if hasattr(self.model_class, field):
                field_attr = getattr(self.model_class, field)
                search_conditions.append(
                    func.lower(field_attr).like(search_pattern)
                )
        
        if search_conditions:
            query = query.where(or_(*search_conditions))
        
        return query

    def _apply_sorting(self, query, sort_field: str, sort_order: str = "desc"):
        """Apply sorting to query."""
        if not hasattr(self.model_class, sort_field):
            sort_field = "created_at"  # Default sort field
        
        field_attr = getattr(self.model_class, sort_field)
        
        if sort_order.lower() == "asc":
            query = query.order_by(field_attr.asc())
        else:
            query = query.order_by(field_attr.desc())
        
        return query

    # Advanced Query Methods
    async def get_all(
        self, 
        user_id: str | None = None,
        include_inactive: bool = False,
        limit: int | None = None,
        skip: int = 0,
        sort_field: str = "created_at",
        sort_order: str = "desc"
    ) -> list[T]:
        """Get all entities with optional filtering and pagination."""
        try:
            query = self._build_base_query(user_id, include_inactive)
            query = self._apply_sorting(query, sort_field, sort_order)
            
            if skip > 0:
                query = query.offset(skip)
            if limit:
                query = query.limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while retrieving {self.model_name} records",
                context={"original_error": str(e)}
            )

    async def get_paginated(
        self,
        user_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: str | None = None,
        search_fields: list[str] | None = None,
        sort_field: str = "created_at",
        sort_order: str = "desc",
        filters: dict[str, Any] | None = None
    ) -> tuple[list[T], int]:
        """Get paginated results with total count."""
        try:
            # Build base query
            query = self._build_base_query(user_id, include_inactive)
            
            # Apply additional filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field) and value is not None:
                        field_attr = getattr(self.model_class, field)
                        if isinstance(value, (list, tuple)):
                            query = query.where(field_attr.in_(value))
                        else:
                            query = query.where(field_attr == value)
            
            # Apply search
            if search and search_fields:
                query = self._apply_search(query, search, search_fields)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply sorting and pagination
            query = self._apply_sorting(query, sort_field, sort_order)
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            entities = list(result.scalars().all())
            
            return entities, total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting paginated {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while retrieving {self.model_name} records",
                context={"original_error": str(e)}
            )

    async def count(
        self, 
        user_id: str | None = None,
        include_inactive: bool = False,
        filters: dict[str, Any] | None = None
    ) -> int:
        """Count entities with optional filtering."""
        try:
            query = self._build_base_query(user_id, include_inactive)
            
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field) and value is not None:
                        field_attr = getattr(self.model_class, field)
                        query = query.where(field_attr == value)
            
            count_query = select(func.count()).select_from(query.subquery())
            result = await self.db.execute(count_query)
            return result.scalar() or 0
            
        except SQLAlchemyError as e:
            logger.error(f"Database error counting {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while counting {self.model_name} records",
                context={"original_error": str(e)}
            )

    async def exists(
        self, 
        entity_id: UUID, 
        user_id: str | None = None
    ) -> bool:
        """Check if entity exists."""
        entity = await self.get_by_id(entity_id, user_id)
        return entity is not None

    async def bulk_create(self, entities: list[T]) -> list[T]:
        """Bulk create multiple entities."""
        try:
            self.db.add_all(entities)
            await self.db.commit()
            
            for entity in entities:
                await self.db.refresh(entity)
            
            logger.info(f"Bulk created {len(entities)} {self.model_name} records")
            return entities
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error bulk creating {self.model_name}: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while bulk creating {self.model_name} records",
                context={"count": len(entities), "original_error": str(e)}
            )

    # Utility Methods
    async def get_field_values(
        self, 
        field_name: str, 
        user_id: str | None = None,
        distinct: bool = True
    ) -> list[Any]:
        """Get unique values for a specific field."""
        try:
            if not hasattr(self.model_class, field_name):
                msg = f"Field '{field_name}' not found in {self.model_name}"
                raise ValueError(msg)
            
            field_attr = getattr(self.model_class, field_name)
            
            if distinct:
                query = select(func.distinct(field_attr))
            else:
                query = select(field_attr)
            
            if user_id and hasattr(self.model_class, 'user_id'):
                query = query.where(self.model_class.user_id == user_id)
            
            result = await self.db.execute(query)
            return [value for value in result.scalars().all() if value is not None]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {field_name} values: {e!s}")
            raise InternalServerError(
                detail=f"Database error occurred while getting {field_name} values",
                context={"field": field_name, "original_error": str(e)}
            )