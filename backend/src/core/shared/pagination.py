from __future__ import annotations

from typing import TypeVar, Generic
from pydantic import BaseModel, Field
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")
    
    @property
    def page(self) -> int:
        """Calculate current page number (1-based)."""
        return (self.skip // self.limit) + 1 if self.limit > 0 else 1


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int = Field(..., description="Current page number (1-based)")
    per_page: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

    @classmethod
    def create(cls, total: int, page: int, per_page: int) -> PaginationMeta:
        """Create pagination metadata from basic parameters."""
        pages = ceil(total / per_page) if total > 0 and per_page > 0 else 0
        
        return cls(
            page=page,
            per_page=per_page,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: list[T] = Field(..., description="List of items for current page")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class SortParams(BaseModel):
    """Standard sorting parameters."""
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class FilterParams(BaseModel):
    """Base filter parameters."""
    include_inactive: bool = Field(False, description="Include inactive records")
    search: str | None = Field(None, description="Search term")


class PaginationHelper:
    """Helper class for pagination calculations."""
    
    @staticmethod
    def calculate_skip(page: int, per_page: int) -> int:
        """Calculate skip value from page number."""
        return max(0, (page - 1) * per_page)
    
    @staticmethod
    def calculate_page(skip: int, per_page: int) -> int:
        """Calculate page number from skip value."""
        return (skip // per_page) + 1 if per_page > 0 else 1
    
    @staticmethod
    def validate_pagination_params(skip: int, limit: int) -> None:
        """Validate pagination parameters."""
        from .exceptions import ValidationError
        
        if skip < 0:
            raise ValidationError(
                detail="Skip parameter cannot be negative",
                context={"skip": skip}
            )
        
        if limit <= 0:
            raise ValidationError(
                detail="Limit parameter must be positive",
                context={"limit": limit}
            )
        
        if limit > 1000:
            raise ValidationError(
                detail="Limit parameter cannot exceed 1000",
                context={"limit": limit, "max_limit": 1000}
            )
    
    @staticmethod
    def create_response(
        items: list[T], 
        total: int, 
        skip: int, 
        limit: int
    ) -> PaginatedResponse[T]:
        """Create a paginated response from query results."""
        page = PaginationHelper.calculate_page(skip, limit)
        meta = PaginationMeta.create(total, page, limit)
        
        return PaginatedResponse[T](
            items=items,
            meta=meta
        )


# Legacy response formats for backward compatibility
class CategoryListResponse(BaseModel, Generic[T]):
    """Legacy category list response format."""
    categories: list[T]
    total: int
    page: int
    per_page: int
    pages: int


class ExpenseListPaginatedResponse(BaseModel, Generic[T]):
    """Legacy expense list response format."""
    expenses: list[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class ContactListResponse(BaseModel, Generic[T]):
    """Legacy contact list response format."""
    contacts: list[T]
    total: int
    page: int
    per_page: int
    pages: int


# Factory functions for legacy responses
def create_legacy_category_response(
    items: list[T], 
    total: int, 
    skip: int, 
    limit: int
) -> CategoryListResponse[T]:
    """Create legacy category list response."""
    page = PaginationHelper.calculate_page(skip, limit)
    pages = ceil(total / limit) if total > 0 and limit > 0 else 0
    
    return CategoryListResponse(
        categories=items,
        total=total,
        page=page,
        per_page=limit,
        pages=pages
    )


def create_legacy_expense_response(
    items: list[T], 
    total: int, 
    skip: int, 
    limit: int
) -> ExpenseListPaginatedResponse[T]:
    """Create legacy expense list response."""
    page = PaginationHelper.calculate_page(skip, limit)
    pages = ceil(total / limit) if total > 0 and limit > 0 else 0
    
    return ExpenseListPaginatedResponse(
        expenses=items,
        total=total,
        page=page,
        per_page=limit,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


def create_legacy_contact_response(
    items: list[T], 
    total: int, 
    skip: int, 
    limit: int
) -> ContactListResponse[T]:
    """Create legacy contact list response."""
    page = PaginationHelper.calculate_page(skip, limit)
    pages = ceil(total / limit) if total > 0 and limit > 0 else 0
    
    return ContactListResponse(
        contacts=items,
        total=total,
        page=page,
        per_page=limit,
        pages=pages
    )
