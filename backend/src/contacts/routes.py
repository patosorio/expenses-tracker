from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from .service import ContactService
from .schemas import ContactCreate, ContactUpdate, ContactResponse, ContactListResponse, ContactSummaryResponse
from .models import ContactType
from ..auth.dependencies import get_current_user
from ..core.database import get_db
from ..users.models import User
from ..core.shared.decorators import api_endpoint
from ..core.shared.pagination import create_legacy_contact_response

router = APIRouter()


@router.post("/", response_model=ContactResponse, status_code=201)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new contact with comprehensive validation."""
    service = ContactService(db)
    contact = await service.create(contact_data.model_dump(), current_user.id)
    return ContactResponse.model_validate(contact)


@router.get("/", response_model=ContactListResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_contacts(
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    search: Optional[str] = Query(None, description="Search in name, email, phone, or tax number"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List contacts with filtering and pagination."""
    service = ContactService(db)
    filters = {}
    if contact_type:
        filters["contact_type"] = contact_type
    contacts, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        sort_field="name",
        sort_order="asc",
        filters=filters
    )
    contact_responses = [ContactResponse.model_validate(contact) for contact in contacts]
    return create_legacy_contact_response(contact_responses, total, skip, limit)


@router.get("/summary", response_model=List[ContactSummaryResponse])
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_contacts_summary(
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get lightweight contact summary for dropdowns/selections."""
    service = ContactService(db)
    contacts = await service.get_contacts_summary(current_user.id, contact_type=contact_type)
    return [ContactSummaryResponse(**contact) for contact in contacts]


@router.get("/{contact_id}", response_model=ContactResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a contact by ID."""
    service = ContactService(db)
    contact = await service.get_by_id_or_raise(contact_id, current_user.id)
    return ContactResponse.model_validate(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_contact(
    contact_id: UUID,
    contact_data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a contact with comprehensive validation."""
    service = ContactService(db)
    contact = await service.update(contact_id, contact_data.model_dump(exclude_unset=True), current_user.id)
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}")
@api_endpoint(handle_exceptions=True, log_calls=True)
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a contact with usage validation."""
    service = ContactService(db)
    await service.delete(contact_id, current_user.id, soft=True)
    return {
        "message": "Contact deleted successfully",
        "contact_id": str(contact_id)
    }


# Additional convenience endpoints

@router.get("/types/{contact_type}", response_model=ContactListResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_contacts_by_type(
    contact_type: ContactType,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all contacts of a specific type (convenience endpoint)."""
    service = ContactService(db)
    filters = {"contact_type": contact_type}
    contacts, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters=filters
    )
    contact_responses = [ContactResponse.model_validate(contact) for contact in contacts]
    return create_legacy_contact_response(contact_responses, total, skip, limit)


@router.get("/search/autocomplete", response_model=List[ContactSummaryResponse])
@api_endpoint(handle_exceptions=True, log_calls=True)
async def search_contacts_autocomplete(
    q: str = Query(..., min_length=2, description="Search term (minimum 2 characters)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search contacts for autocomplete functionality."""
    service = ContactService(db)
    filters = {}
    if contact_type:
        filters["contact_type"] = contact_type
    contacts, _ = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=limit,
        search=q,
        filters=filters
    )
    return [ContactSummaryResponse(
        id=contact.id,
        name=contact.name,
        contact_type=contact.contact_type,
        email=contact.email,
        phone=contact.phone
    ) for contact in contacts]


@router.get("/stats/overview")
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_contacts_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contact statistics for dashboard."""
    service = ContactService(db)
    # Get contacts by type
    customers, _ = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=1000,
        filters={"contact_type": ContactType.CUSTOMER}
    )
    suppliers, _ = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=1000,
        filters={"contact_type": ContactType.SUPPLIER}
    )
    vendors, _ = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=1000,
        filters={"contact_type": ContactType.VENDOR}
    )
    all_contacts, total = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=1000
    )
    return {
        "total_contacts": total,
        "customers": len(customers),
        "suppliers": len(suppliers),
        "vendors": len(vendors),
        "contacts_by_type": {
            "CUSTOMER": len(customers),
            "SUPPLIER": len(suppliers),
            "VENDOR": len(vendors)
        }
    }


@router.post("/{contact_id}/archive")
@api_endpoint(handle_exceptions=True, log_calls=True)
async def archive_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive a contact (alias for delete)."""
    service = ContactService(db)
    await service.delete(contact_id, current_user.id, soft=True)
    return {
        "message": "Contact archived successfully",
        "contact_id": str(contact_id)
    }


@router.get("/export/csv")
@api_endpoint(handle_exceptions=True, log_calls=True)
async def export_contacts_csv(
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export contacts to CSV format."""
    service = ContactService(db)
    filters = {}
    if contact_type:
        filters["contact_type"] = contact_type
    contacts, _ = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=10000,
        filters=filters
    )
    # TODO: generate and return a CSV file
    # For now, return a simple response
    return {
        "message": "CSV export functionality - implement file generation",
        "contact_count": len(contacts),
        "contact_type": contact_type.value if contact_type else "ALL"
    }
