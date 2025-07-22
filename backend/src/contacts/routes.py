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

router = APIRouter()


@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new contact with comprehensive validation."""
    service = ContactService(db)
    return await service.create_contact(contact_data, current_user.id)


@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    search: Optional[str] = Query(None, description="Search in name, email, phone, or tax number"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List contacts with filtering and pagination."""
    service = ContactService(db)
    skip = (page - 1) * per_page
    
    contacts, total = await service.list_contacts(
        user_id=current_user.id,
        contact_type=contact_type,
        search=search,
        skip=skip,
        limit=per_page
    )
    
    return ContactListResponse(
        contacts=contacts,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 0
    )


@router.get("/summary", response_model=List[ContactSummaryResponse])
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
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a contact by ID."""
    service = ContactService(db)
    return await service.get_contact(contact_id, current_user.id)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    contact_data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a contact with comprehensive validation."""
    service = ContactService(db)
    return await service.update_contact(contact_id, contact_data, current_user.id)


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a contact with usage validation."""
    service = ContactService(db)
    await service.delete_contact(contact_id, current_user.id)
    return {
        "message": "Contact deleted successfully",
        "contact_id": str(contact_id)
    }


# Additional convenience endpoints

@router.get("/types/{contact_type}", response_model=List[ContactResponse])
async def get_contacts_by_type(
    contact_type: ContactType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all contacts of a specific type (convenience endpoint)."""
    service = ContactService(db)
    contacts, _ = await service.list_contacts(
        user_id=current_user.id,
        contact_type=contact_type,
        skip=0,
        limit=1000  # High limit for type-specific queries
    )
    return contacts


@router.get("/search/autocomplete", response_model=List[ContactSummaryResponse])
async def search_contacts_autocomplete(
    q: str = Query(..., min_length=2, description="Search term (minimum 2 characters)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search contacts for autocomplete functionality."""
    service = ContactService(db)
    
    # Use the list_contacts method with search term
    contacts, _ = await service.list_contacts(
        user_id=current_user.id,
        contact_type=contact_type,
        search=q,
        skip=0,
        limit=limit
    )
    
    # Convert to summary format
    return [
        ContactSummaryResponse(
            id=contact.id,
            name=contact.name,
            contact_type=contact.contact_type,
            email=contact.email,
            phone=contact.phone
        )
        for contact in contacts
    ]


@router.get("/stats/overview")
async def get_contacts_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contact statistics for dashboard."""
    service = ContactService(db)
    
    # Get contacts by type
    customers, _ = await service.list_contacts(
        user_id=current_user.id,
        contact_type=ContactType.CUSTOMER,
        skip=0,
        limit=1000
    )
    
    suppliers, _ = await service.list_contacts(
        user_id=current_user.id,
        contact_type=ContactType.SUPPLIER,
        skip=0,
        limit=1000
    )
    
    vendors, _ = await service.list_contacts(
        user_id=current_user.id,
        contact_type=ContactType.VENDOR,
        skip=0,
        limit=1000
    )
    
    all_contacts, total = await service.list_contacts(
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
async def archive_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive a contact (alias for delete)."""
    service = ContactService(db)
    await service.delete_contact(contact_id, current_user.id)
    return {
        "message": "Contact archived successfully",
        "contact_id": str(contact_id)
    }


@router.get("/export/csv")
async def export_contacts_csv(
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export contacts to CSV format."""
    service = ContactService(db)
    contacts, _ = await service.list_contacts(
        user_id=current_user.id,
        contact_type=contact_type,
        skip=0,
        limit=10000  # High limit for export
    )
    
    # TODO: generate and return a CSV file
    # For now, return a simple response
    return {
        "message": "CSV export functionality - implement file generation",
        "contact_count": len(contacts),
        "contact_type": contact_type.value if contact_type else "ALL"
    }