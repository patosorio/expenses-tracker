from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from .models import Contact, ContactType
from .schemas import ContactCreate, ContactUpdate, ContactResponse
from src.exceptions import ContactNotFoundError, ContactAlreadyExistsError


class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_contact(self, contact_data: ContactCreate, user_id: str) -> ContactResponse:
        """Create a new contact"""
        # Check for duplicate name within user's contacts
        existing = await self.db.execute(
            select(Contact).where(
                Contact.user_id == user_id,
                Contact.name == contact_data.name,
                Contact.is_active == True
            )
        )
        if existing.scalar_one_or_none():
            raise ContactAlreadyExistsError(f"Contact '{contact_data.name}' already exists")

        contact = Contact(
            **contact_data.model_dump(),
            user_id=user_id
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        
        return ContactResponse.model_validate(contact)

    async def get_contact(self, contact_id: UUID, user_id: str) -> ContactResponse:
        """Get a contact by ID"""
        result = await self.db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.user_id == user_id,
                Contact.is_active == True
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            raise ContactNotFoundError("Contact not found")
        
        return ContactResponse.model_validate(contact)

    async def list_contacts(
        self,
        user_id: str,
        contact_type: Optional[ContactType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[ContactResponse], int]:
        """List contacts with filtering"""
        query = select(Contact).where(
            Contact.user_id == user_id,
            Contact.is_active == True
        )
        
        if contact_type:
            query = query.where(Contact.contact_type == contact_type)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Contact.name.ilike(search_term),
                    Contact.email.ilike(search_term),
                    Contact.tax_number.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar()
        
        # Get paginated results
        result = await self.db.execute(
            query.order_by(Contact.name).offset(skip).limit(limit)
        )
        contacts = result.scalars().all()
        
        return [ContactResponse.model_validate(contact) for contact in contacts], total_count

    async def update_contact(
        self,
        contact_id: UUID,
        contact_data: ContactUpdate,
        user_id: str
    ) -> ContactResponse:
        """Update a contact"""
        result = await self.db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.user_id == user_id,
                Contact.is_active == True
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            raise ContactNotFoundError("Contact not found")

        # Check for duplicate name if name is being updated
        update_data = contact_data.model_dump(exclude_unset=True)
        if 'name' in update_data and update_data['name'] != contact.name:
            existing = await self.db.execute(
                select(Contact).where(
                    Contact.user_id == user_id,
                    Contact.name == update_data['name'],
                    Contact.id != contact_id,
                    Contact.is_active == True
                )
            )
            if existing.scalar_one_or_none():
                raise ContactAlreadyExistsError(f"Contact '{update_data['name']}' already exists")

        for field, value in update_data.items():
            setattr(contact, field, value)

        await self.db.commit()
        await self.db.refresh(contact)
        
        return ContactResponse.model_validate(contact)

    async def delete_contact(self, contact_id: UUID, user_id: str) -> None:
        """Soft delete a contact"""
        result = await self.db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.user_id == user_id,
                Contact.is_active == True
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            raise ContactNotFoundError("Contact not found")

        contact.is_active = False
        await self.db.commit()

    async def get_contacts_summary(
        self,
        user_id: str,
        contact_type: Optional[ContactType] = None
    ) -> List[dict]:
        """Get lightweight contact summary for dropdowns"""
        query = select(
            Contact.id,
            Contact.name,
            Contact.contact_type,
            Contact.email,
            Contact.phone
        ).where(
            Contact.user_id == user_id,
            Contact.is_active == True
        )
        
        if contact_type:
            query = query.where(Contact.contact_type == contact_type)
        
        result = await self.db.execute(
            query.order_by(Contact.name)
        )
        
        return [
            {
                "id": row.id,
                "name": row.name,
                "contact_type": row.contact_type,
                "email": row.email,
                "phone": row.phone
            }
            for row in result.all()
        ]
