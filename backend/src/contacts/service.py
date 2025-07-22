import re
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Contact, ContactType
from .repository import ContactRepository
from .schemas import ContactCreate, ContactUpdate, ContactResponse
from .exceptions import *
from ..core.shared.exceptions import ValidationError, InternalServerError

logger = logging.getLogger(__name__)


class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.contact_repo = ContactRepository(db)

    async def create_contact(self, contact_data: ContactCreate, user_id: str) -> ContactResponse:
        """Create a new contact"""
        try:
            # Validate input data
            await self._validate_contact_data(contact_data)
            await self._check_duplicate_name(user_id, contact_data.name)

            if contact_data.email:
                await self._check_duplicate_email(user_id, contact_data.email)

            # Create contact model
            contact = Contact(
                **contact_data.model_dump(),
                user_id=user_id
            )

            # Delegate to repository
            created_contact = await self.contact_repo.create(contact)
            logger.info(f"Contact created successfully: {created_contact.id} for user {user_id}")

            return ContactResponse.model_validate(created_contact)
            
        except (
            ContactValidationError, ContactAlreadyExistsError, DuplicateContactEmailError,
            InvalidContactEmailError, InvalidContactPhoneError, ContactTaxNumberError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating contact for user {user_id}: {str(e)}", exc_info=True)
            raise InternalServerError(
                detail="Failed to create contact due to internal error",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_contact(self, contact_id: UUID, user_id: str) -> ContactResponse:
        """Get a contact by ID"""
        try:
            contact = await self._get_contact_or_raise(contact_id, user_id)
            return ContactResponse.model_validate(contact)
            
        except ContactNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting contact {contact_id} for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve contact",
                context={"contact_id": str(contact_id), "user_id": user_id, "original_error": str(e)}
            )

    async def list_contacts(
        self,
        user_id: str,
        contact_type: Optional[ContactType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ContactResponse], int]:
        """List contacts with filtering and pagination validation"""
        try:
            # Pagination parameters
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
            
            # Validate search parameter
            if search and len(search.strip()) < 2:
                raise InvalidContactSearchError(
                    detail="Search term must be at least 2 characters long",
                    context={"search": search, "length": len(search.strip())}
                )
            
            # Delegate to repository
            contacts, total_count = await self.contact_repo.get_contacts(
                user_id, contact_type, search, skip, limit
            )
            
            contact_responses = [ContactResponse.model_validate(contact) for contact in contacts]
            return contact_responses, total_count

        except (ValidationError, InvalidContactSearchError):
            raise
        except Exception as e:
            logger.error(f"Error listing contacts for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve contacts",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def update_contact(
        self,
        contact_id: UUID,
        contact_data: ContactUpdate,
        user_id: str
    ) -> ContactResponse:
        """Update a contact with validation"""
        try:
            # Get contact from repository
            contact = await self.contact_repo.get_by_id(contact_id, user_id)
            
            # Validate update data
            update_data = contact_data.model_dump(exclude_unset=True)
            if not update_data:
                raise ContactValidationError(
                    detail="No valid fields provided for update",
                    context={"contact_id": str(contact_id), "user_id": user_id}
                )
            # Validate updated contact data
            if update_data:
                await self._validate_update_data(update_data)

            # Check for duplicate name if name is being updated
            if 'name' in update_data and update_data['name'] != contact.name:
                await self._check_duplicate_name(
                    user_id, update_data['name'], exclude_id=contact_id
                )

            # Check for duplicate email if email is being updated
            if 'email' in update_data and update_data.get('email') != contact.email:
                if update_data['email']:  # Only check if new email is not empty
                    await self._check_duplicate_email(
                        user_id, update_data['email'], exclude_id=contact_id
                    )
            
            # Apply updates
            for field, value in update_data.items():
                setattr(contact, field, value)

            # Delegate to repository
            updated_contact = await self.contact_repo.update(contact)
            logger.info(f'Contact updated succesfully: {contact_id} for user {user_id}')

            return ContactResponse.model_validate(updated_contact)

        except (
            ContactNotFoundError, ContactValidationError, ContactAlreadyExistsError,
            DuplicateContactEmailError, InvalidContactEmailError, InvalidContactPhoneError
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating contact {contact_id}: {str(e)}", exc_info=True)
            raise ContactUpdateError(
                detail="Failed to update contact due to internal error",
                context={"contact_id": str(contact_id), "user_id": user_id, "original_error": str(e)}
            )

    async def delete_contact(self, contact_id: UUID, user_id: str) -> None:
        """Soft delete a contact with usage validation"""
        try:
            # Get existing contact
            contact = await self._get_contact_or_raise(contact_id, user_id)
            
            # Business logic: Check if contact is in use (has expenses or invoices)
            if await self.contact_repo.is_contact_in_use(contact_id):
                raise ContactInUseError(
                    detail="Cannot delete contact that has associated expenses or invoices",
                    context={"contact_id": str(contact_id)}
                )
            
            # Delegate to repository
            await self.contact_repo.delete(contact)
            logger.info(f"Contact deleted successfully: {contact_id} for user {user_id}")
            
        except (ContactNotFoundError, ContactInUseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting contact {contact_id}: {str(e)}", exc_info=True)
            raise ContactDeleteError(
                detail="Failed to delete contact due to internal error",
                context={"contact_id": str(contact_id), "user_id": user_id, "original_error": str(e)}
            )

    async def get_contacts_summary(
        self,
        user_id: str,
        contact_type: Optional[ContactType] = None
    ) -> List[dict]:
        """Get lightweight contact summary for dropdowns."""
        try:
            return await self.contact_repo.get_contacts_summary(user_id, contact_type)
            
        except Exception as e:
            logger.error(f"Error getting contacts summary for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve contacts summary",
                context={"user_id": user_id, "original_error": str(e)}
            )
    
    # Private helper methods for validation

    async def _get_contact_or_raise(self, contact_id: UUID, user_id: str) -> Contact:
        """Get contact or raise ContactNotFoundError."""
        contact = await self.contact_repo.get_by_id(contact_id, user_id)
        if not contact:
            raise ContactNotFoundError(
                detail=f"Contact with ID {contact_id} not found",
                context={"contact_id": str(contact_id), "user_id": user_id}
            )
        return contact

    async def _validate_contact_data(self, contact_data: ContactCreate) -> None:
        """Validate contact creation data."""
        # Validate name
        if not contact_data.name or not contact_data.name.strip():
            raise ContactValidationError(
                detail="Contact name cannot be empty",
                context={"name": contact_data.name}
            )
        
        if len(contact_data.name.strip()) > 100:
            raise ContactValidationError(
                detail="Contact name must be 100 characters or less",
                context={"name": contact_data.name, "length": len(contact_data.name)}
            )

        # Validate email if provided
        if contact_data.email:
            self._validate_email_format(contact_data.email)

        # Validate phone if provided
        if contact_data.phone:
            self._validate_phone_format(contact_data.phone)

        # Validate tax number if provided
        if contact_data.tax_number:
            self._validate_tax_number_format(contact_data.tax_number)

    async def _validate_update_data(self, update_data: dict) -> None:
        """Validate contact update data."""
        if 'name' in update_data:
            if not update_data['name'] or not update_data['name'].strip():
                raise ContactValidationError(
                    detail="Contact name cannot be empty",
                    context={"name": update_data['name']}
                )
        
        if 'email' in update_data and update_data['email']:
            self._validate_email_format(update_data['email'])

        if 'phone' in update_data and update_data['phone']:
            self._validate_phone_format(update_data['phone'])

        if 'tax_number' in update_data and update_data['tax_number']:
            self._validate_tax_number_format(update_data['tax_number'])

    def _validate_email_format(self, email: str) -> None:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            raise InvalidContactEmailError(
                detail="Invalid email format",
                context={"email": email}
            )

    def _validate_phone_format(self, phone: str) -> None:
        """Validate phone number format."""
        # Basic phone validation - adjust pattern based on your requirements
        phone_cleaned = re.sub(r'[^\d+\-\s\(\)]', '', phone.strip())
        if len(phone_cleaned) < 7 or len(phone_cleaned) > 20:
            raise InvalidContactPhoneError(
                detail="Phone number must be between 7 and 20 characters",
                context={"phone": phone, "cleaned_length": len(phone_cleaned)}
            )

    def _validate_tax_number_format(self, tax_number: str) -> None:
        """Validate tax number format."""
        # Basic tax number validation - adjust based on your requirements
        tax_cleaned = re.sub(r'[^\w\-]', '', tax_number.strip())
        if len(tax_cleaned) < 5 or len(tax_cleaned) > 20:
            raise ContactTaxNumberError(
                detail="Tax number must be between 5 and 20 alphanumeric characters",
                context={"tax_number": tax_number, "cleaned_length": len(tax_cleaned)}
            )

    async def _check_duplicate_name(
        self, 
        user_id: str, 
        name: str, 
        exclude_id: Optional[UUID] = None
    ) -> None:
        """Check for duplicate contact name."""
        try:
            is_duplicate = await self.contact_repo.check_duplicate_name(user_id, name, exclude_id)
            if is_duplicate:
                raise ContactAlreadyExistsError(
                    detail=f"Contact '{name}' already exists",
                    context={"name": name, "user_id": user_id}
                )
        except ContactAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Error checking duplicate name: {str(e)}")
            raise InternalServerError(
                detail="Failed to validate contact name uniqueness",
                context={"name": name, "original_error": str(e)}
            )

    async def _check_duplicate_email(
        self, 
        user_id: str, 
        email: str, 
        exclude_id: Optional[UUID] = None
    ) -> None:
        """Check for duplicate contact email."""
        try:
            is_duplicate = await self.contact_repo.check_duplicate_email(user_id, email, exclude_id)
            if is_duplicate:
                raise DuplicateContactEmailError(
                    detail=f"Contact with email '{email}' already exists",
                    context={"email": email, "user_id": user_id}
                )
        except DuplicateContactEmailError:
            raise
        except Exception as e:
            logger.error(f"Error checking duplicate email: {str(e)}")
            raise InternalServerError(
                detail="Failed to validate email uniqueness",
                context={"email": email, "original_error": str(e)}
            )
