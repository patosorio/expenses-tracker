# backend/src/core/shared/base_service.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import TypeVar, Generic, Type, Any
from uuid import UUID
import logging

from .base_repository import BaseRepository
from .exceptions import ValidationError, NotFoundError, InternalServerError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=DeclarativeBase)
R = TypeVar('R', bound=BaseRepository[Any])


class BaseService(Generic[T, R]):
    """Base service with common business logic patterns."""
    
    def __init__(
        self, 
        db: AsyncSession, 
        repository_class: Type[R],
        model_class: Type[T]
    ) -> None:
        self.db = db
        self.repository: R = repository_class(db, model_class)
        self.model_class = model_class
        self.model_name = model_class.__name__.lower()

    # Core CRUD Operations
    async def create(self, entity_data: dict[str, Any], user_id: str) -> T:
        """Create entity with user validation."""
        try:
            # Add user_id if model supports multi-tenancy
            if hasattr(self.model_class, 'user_id'):
                entity_data['user_id'] = user_id
            
            # Create entity instance
            entity = self.model_class(**entity_data)
            
            # Delegate to repository
            return await self.repository.create(entity)
            
        except Exception as e:
            logger.error(f"Error creating {self.model_name} for user {user_id}: {e!s}")
            raise InternalServerError(
                detail=f"Failed to create {self.model_name}",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_by_id(
        self, 
        entity_id: UUID, 
        user_id: str,
        include_inactive: bool = False
    ) -> T | None:
        """Get entity by ID with user isolation."""
        return await self.repository.get_by_id(entity_id, user_id, include_inactive)

    async def get_by_id_or_raise(
        self, 
        entity_id: UUID, 
        user_id: str,
        include_inactive: bool = False
    ) -> T:
        """Get entity by ID or raise NotFoundError."""
        entity = await self.get_by_id(entity_id, user_id, include_inactive)
        if not entity:
            raise NotFoundError(
                detail=f"{self.model_name.title()} not found",
                context={"entity_id": str(entity_id), "user_id": user_id}
            )
        return entity

    async def update(
        self, 
        entity_id: UUID, 
        update_data: dict[str, Any], 
        user_id: str
    ) -> T:
        """Update entity with user validation."""
        try:
            # Get entity with user validation
            entity = await self.get_by_id_or_raise(entity_id, user_id)
            
            # Filter out None values and remove read-only fields
            filtered_data = {
                key: value for key, value in update_data.items() 
                if value is not None and key not in ['id', 'created_at', 'user_id']
            }
            
            # Update entity
            return await self.repository.update(entity, filtered_data)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating {self.model_name} {entity_id}: {e!s}")
            raise InternalServerError(
                detail=f"Failed to update {self.model_name}",
                context={"entity_id": str(entity_id), "user_id": user_id, "original_error": str(e)}
            )

    async def delete(
        self, 
        entity_id: UUID, 
        user_id: str, 
        soft: bool = True
    ) -> None:
        """Delete entity with user validation."""
        try:
            # Get entity with user validation
            entity = await self.get_by_id_or_raise(entity_id, user_id)
            
            if soft and hasattr(entity, 'is_active'):
                await self.repository.soft_delete(entity)
                logger.info(f"Soft deleted {self.model_name} {entity_id}")
            else:
                await self.repository.hard_delete(entity)
                logger.info(f"Hard deleted {self.model_name} {entity_id}")
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting {self.model_name} {entity_id}: {e!s}")
            raise InternalServerError(
                detail=f"Failed to delete {self.model_name}",
                context={"entity_id": str(entity_id), "user_id": user_id, "original_error": str(e)}
            )

    # List and Pagination
    async def get_all(
        self, 
        user_id: str,
        include_inactive: bool = False,
        limit: int | None = None,
        sort_field: str = "created_at",
        sort_order: str = "desc"
    ) -> list[T]:
        """Get all entities for user."""
        try:
            return await self.repository.get_all(
                user_id=user_id,
                include_inactive=include_inactive,
                limit=limit,
                sort_field=sort_field,
                sort_order=sort_order
            )
        except Exception as e:
            logger.error(f"Error getting all {self.model_name} for user {user_id}: {e!s}")
            raise InternalServerError(
                detail=f"Failed to retrieve {self.model_name} records",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_paginated(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: str | None = None,
        search_fields: list[str] | None = None,
        sort_field: str = "created_at",
        sort_order: str = "desc",
        filters: dict[str, Any] | None = None
    ) -> tuple[list[T], int]:
        """Get paginated results with filtering."""
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
            
            return await self.repository.get_paginated(
                user_id=user_id,
                skip=skip,
                limit=limit,
                include_inactive=include_inactive,
                search=search,
                search_fields=search_fields or self._get_default_search_fields(),
                sort_field=sort_field,
                sort_order=sort_order,
                filters=filters
            )
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting paginated {self.model_name} for user {user_id}: {e!s}")
            raise InternalServerError(
                detail=f"Failed to retrieve {self.model_name} records",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def count(
        self, 
        user_id: str,
        include_inactive: bool = False,
        filters: dict[str, Any] | None = None
    ) -> int:
        """Count entities with filtering."""
        try:
            return await self.repository.count(
                user_id=user_id,
                include_inactive=include_inactive,
                filters=filters
            )
        except Exception as e:
            logger.error(f"Error counting {self.model_name} for user {user_id}: {e!s}")
            raise InternalServerError(
                detail=f"Failed to count {self.model_name} records",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def exists(self, entity_id: UUID, user_id: str) -> bool:
        """Check if entity exists for user."""
        return await self.repository.exists(entity_id, user_id)

    # Validation Helpers
    def _validate_required_fields(self, data: dict[str, Any], required_fields: list[str]) -> None:
        """Validate required fields are present."""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            raise ValidationError(
                detail=f"Required fields missing: {', '.join(missing_fields)}",
                context={"missing_fields": missing_fields}
            )

    def _validate_field_length(self, data: dict[str, Any], field_limits: dict[str, int]) -> None:
        """Validate field length constraints."""
        for field, max_length in field_limits.items():
            if field in data and data[field] and len(str(data[field])) > max_length:
                raise ValidationError(
                    detail=f"Field '{field}' exceeds maximum length of {max_length}",
                    context={"field": field, "max_length": max_length, "actual_length": len(str(data[field]))}
                )

    def _validate_enum_values(self, data: dict[str, Any], enum_fields: dict[str, list[str]]) -> None:
        """Validate enum field values."""
        for field, valid_values in enum_fields.items():
            if field in data and data[field] and data[field] not in valid_values:
                raise ValidationError(
                    detail=f"Invalid value for '{field}'. Must be one of: {', '.join(valid_values)}",
                    context={"field": field, "value": data[field], "valid_values": valid_values}
                )

    def _get_default_search_fields(self) -> list[str]:
        """Get default search fields for the model. Override in subclasses."""
        search_fields = []
        
        # Common searchable fields
        common_fields = ['name', 'title', 'description', 'email']
        for field in common_fields:
            if hasattr(self.model_class, field):
                search_fields.append(field)
        
        return search_fields

    # User Isolation Validation
    async def _validate_user_ownership(self, entity_id: UUID, user_id: str) -> T:
        """Validate user owns the entity."""
        entity = await self.get_by_id(entity_id, user_id)
        if not entity:
            raise NotFoundError(
                detail=f"{self.model_name.title()} not found",
                context={"entity_id": str(entity_id), "user_id": user_id}
            )
        return entity

    async def _validate_unique_constraint(
        self, 
        user_id: str, 
        field_name: str, 
        value: Any,
        exclude_id: UUID | None = None
    ) -> None:
        """Validate unique constraint within user scope."""
        try:
            filters = {field_name: value}
            entities, _ = await self.repository.get_paginated(
                user_id=user_id,
                limit=1,
                filters=filters
            )
            
            # If we found an entity, check if it's not the one we're updating
            if entities:
                entity = entities[0]
                if exclude_id is None or entity.id != exclude_id:
                    raise ValidationError(
                        detail=f"{self.model_name.title()} with this {field_name} already exists",
                        context={
                            "field": field_name,
                            "value": value,
                            "existing_id": str(entity.id)
                        }
                    )
                    
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating unique constraint: {e!s}")
            raise InternalServerError(
                detail="Failed to validate unique constraint",
                context={"field": field_name, "value": value, "original_error": str(e)}
            )

    # Business Logic Hooks - Override in subclasses
    async def _pre_create_validation(self, entity_data: dict[str, Any], user_id: str) -> None:
        """Override in subclasses for custom pre-create validation."""
        pass

    async def _post_create_actions(self, entity: T, user_id: str) -> None:
        """Override in subclasses for custom post-create actions."""
        pass

    async def _pre_update_validation(
        self, 
        entity: T, 
        update_data: dict[str, Any], 
        user_id: str
    ) -> None:
        """Override in subclasses for custom pre-update validation."""
        pass

    # TODO:
    async def _post_update_actions(self, entity: T, user_id: str) -> None:
        """Override in subclasses for custom post-update actions."""
        pass

    async def _pre_delete_validation(self, entity: T, user_id: str) -> None:
        """Override in subclasses for custom pre-delete validation."""
        pass

    async def _post_delete_actions(self, entity_id: UUID, user_id: str) -> None:
        """Override in subclasses for custom post-delete actions."""
        pass