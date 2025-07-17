from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from uuid import UUID

from .service import ContactService
from src.exceptions import ContactNotFoundError, ContactAlreadyExistsError
from .schemas import ContactCreate, ContactUpdate, ContactResponse, ContactListResponse, ContactSummaryResponse
from .models import ContactType
from src.auth.dependencies import get_current_user
from src.database import get_db


router = APIRouter(tags=["contacts"])


@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new contact"""
    service = ContactService(db)
    try:
        return await service.create_contact(contact_data, current_user.id)
    except ContactAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error creating contact: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create contact: {str(e)}")


@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    search: Optional[str] = Query(None, description="Search in name, email, or tax number"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List contacts with filtering and pagination"""
    service = ContactService(db)
    skip = (page - 1) * per_page
    
    contacts, total = await service.list_contacts(
        current_user.id,
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
        pages=(total + per_page - 1) // per_page
    )


@router.get("/summary", response_model=List[ContactSummaryResponse])
async def get_contacts_summary(
    contact_type: Optional[ContactType] = Query(None, description="Filter by contact type"),
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get lightweight contact summary for dropdowns/selections"""
    service = ContactService(db)
    contacts = await service.get_contacts_summary(current_user.id, contact_type=contact_type)
    return [ContactSummaryResponse(**contact) for contact in contacts]


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a contact by ID"""
    service = ContactService(db)
    try:
        return await service.get_contact(contact_id, current_user.id)
    except ContactNotFoundError:
        raise HTTPException(status_code=404, detail="Contact not found")


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    contact_data: ContactUpdate,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a contact"""
    service = ContactService(db)
    try:
        return await service.update_contact(contact_id, contact_data, current_user.id)
    except ContactNotFoundError:
        raise HTTPException(status_code=404, detail="Contact not found")
    except ContactAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: UUID,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a contact"""
    service = ContactService(db)
    try:
        await service.delete_contact(contact_id, current_user.id)
        return {"message": "Contact deleted successfully"}
    except ContactNotFoundError:
        raise HTTPException(status_code=404, detail="Contact not found")
