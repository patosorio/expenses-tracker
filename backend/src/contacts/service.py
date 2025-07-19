from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .models import Contact, ContactType
from .repository import ContactRepository
from .schemas import ContactCreate, ContactUpdate, ContactResponse
from .exceptions import (
    ContactNotFoundError, ContactValidationError, ContactAlreadyExistsError,
    ContactUpdateError, ContactDeleteError, DuplicateContactEmailError
)

logger = logging.getLogger(__name__)


class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.contact_repo = ContactRepository(self.db)

    async def create_contact(self, contact_data: ContactCreate, user_id: str) -> ContactResponse:
        """Create a new contact"""
        try:
            # Business logic: Check for duplicate name within user's contacts
            is_duplicate_name = await self.contact_repo.check_duplicate_name(user_id, contact_data.name)
            
            if is_duplicate_name:
                raise ContactAlreadyExistsError(f"Contact '{contact_data.name}' already exists")

            # Business logic: Check for duplicate email if provided
            if contact_data.email:
                is_duplicate_email = await self.contact_repo.check_duplicate_email(user_id, contact_data.email)
                
                if is_duplicate_email:
                    raise DuplicateContactEmailError(f"Contact with email '{contact_data.email}' already exists")

            # Business logic: Create contact model
            contact = Contact(
                **contact_data.model_dump(),
                user_id=user_id
            )
            
            # Delegate to repository for data access
            created_contact = await self.contact_repo.create(contact)
            
            return ContactResponse.model_validate(created_contact)
            
        except Exception as e:
            logger.error(f"Error creating contact for user {user_id}: {str(e)}")
            raise

    async def get_contact(self, contact_id: UUID, user_id: str) -> ContactResponse:
        """Get a contact by ID"""
        try:
            # Delegate to repository for data access
            contact = await self.contact_repo.get_by_id(contact_id, user_id)
            
            if not contact:
                raise ContactNotFoundError("Contact not found")
            
            return ContactResponse.model_validate(contact)
            
        except Exception as e:
            logger.error(f"Error getting contact {contact_id} for user {user_id}: {str(e)}")
            raise

    async def list_contacts(
        self,
        user_id: str,
        contact_type: Optional[ContactType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ContactResponse], int]:
        """List contacts with filtering"""
        try:
            # Delegate to repository for data access
            contacts, total_count = await self.contact_repo.get_contacts(
                user_id, contact_type, search, skip, limit
            )
            
            return [ContactResponse.model_validate(contact) for contact in contacts], total_count
            
        except Exception as e:
            logger.error(f"Error listing contacts for user {user_id}: {str(e)}")
            raise

    async def update_contact(
        self,
        contact_id: UUID,
        contact_data: ContactUpdate,
        user_id: str
    ) -> ContactResponse:
        """Update a contact"""
        try:
            # Get contact from repository
            contact = await self.contact_repo.get_by_id(contact_id, user_id)
            
            if not contact:
                raise ContactNotFoundError("Contact not found")

            # Business logic: Check for duplicate name if name is being updated
            update_data = contact_data.model_dump(exclude_unset=True)
            if 'name' in update_data and update_data['name'] != contact.name:
                is_duplicate_name = await self.contact_repo.check_duplicate_name(
                    user_id, update_data['name'], contact_id
                )
                if is_duplicate_name:
                    raise ContactAlreadyExistsError(f"Contact '{update_data['name']}' already exists")

            # Business logic: Check for duplicate email if email is being updated
            if 'email' in update_data and update_data['email'] != contact.email:
                is_duplicate_email = await self.contact_repo.check_duplicate_email(
                    user_id, update_data['email'], contact_id
                )
                if is_duplicate_email:
                    raise DuplicateContactEmailError(f"Contact with email '{update_data['email']}' already exists")

            # Business logic: Update fields
            for field, value in update_data.items():
                setattr(contact, field, value)

            # Delegate to repository for data access
            updated_contact = await self.contact_repo.update(contact)
            
            return ContactResponse.model_validate(updated_contact)
            
        except Exception as e:
            logger.error(f"Error updating contact {contact_id} for user {user_id}: {str(e)}")
            raise ContactUpdateError(f"Failed to update contact: {str(e)}")

    async def delete_contact(self, contact_id: UUID, user_id: str) -> None:
        """Soft delete a contact"""
        try:
            # Get contact from repository
            contact = await self.contact_repo.get_by_id(contact_id, user_id)
            
            if not contact:
                raise ContactNotFoundError("Contact not found")

            # Delegate to repository for data access
            await self.contact_repo.delete(contact)
            
        except Exception as e:
            logger.error(f"Error deleting contact {contact_id} for user {user_id}: {str(e)}")
            raise ContactDeleteError(f"Failed to delete contact: {str(e)}")

    async def get_contacts_summary(
        self,
        user_id: str,
        contact_type: Optional[ContactType] = None
    ) -> List[dict]:
        """Get lightweight contact summary for dropdowns"""
        try:
            # Delegate to repository for data access
            return await self.contact_repo.get_contacts_summary(user_id, contact_type)
            
        except Exception as e:
            logger.error(f"Error getting contacts summary for user {user_id}: {str(e)}")
            raise
