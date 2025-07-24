import re
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Contact, ContactType
from .repository import ContactRepository
from .schemas import ContactCreate, ContactUpdate
from .exceptions import *
from ..core.shared.base_service import BaseService
from ..core.shared.exceptions import ValidationError, InternalServerError

logger = logging.getLogger(__name__)

MAX_CONTACT_NAME_LENGTH = 100

class ContactService(BaseService[Contact, ContactRepository]):
    """Contact service with business logic extending BaseService."""
    def __init__(self, db: AsyncSession):
        """Initialize ContactService with database session."""
        super().__init__(db, ContactRepository, Contact)

    async def get_contacts_summary(
        self,
        user_id: str,
        contact_type: ContactType | None = None
    ) -> List[dict]:
        """Get lightweight contact summary for dropdowns."""
        try:
            return await self.repository.get_contacts_summary(user_id, contact_type)
        except Exception as e:
            logger.error(f"Error getting contacts summary for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Failed to retrieve contacts summary",
                context={"user_id": user_id, "original_error": str(e)}
            )

    # Validation hooks
    async def _pre_create_validation(self, entity_data: Dict[str, Any], user_id: str) -> None:
        """Contact-specific pre-create validation."""
        await self._validate_contact_data(entity_data)
        await self._check_duplicate_name(user_id, entity_data["name"])
        if entity_data.get("email"):
            await self._check_duplicate_email(user_id, entity_data["email"])

    async def _pre_update_validation(self, entity: Contact, update_data: Dict[str, Any], user_id: str) -> None:
        """Contact-specific pre-update validation."""
        if not update_data:
            raise ContactValidationError(
                detail="No valid fields provided for update",
                context={"contact_id": str(entity.id), "user_id": user_id}
            )
        await self._validate_update_data(update_data)
        if "name" in update_data and update_data["name"] != entity.name:
            await self._check_duplicate_name(user_id, update_data["name"], exclude_id=entity.id)
        if "email" in update_data and update_data.get("email") != entity.email:
            if update_data["email"]:
                await self._check_duplicate_email(user_id, update_data["email"], exclude_id=entity.id)

    async def _pre_delete_validation(self, entity: Contact, user_id: str) -> None:
        """Contact-specific pre-delete validation."""
        if await self.repository.is_contact_in_use(entity.id):
            raise ContactInUseError(
                detail="Cannot delete contact that has associated expenses or invoices",
                context={"contact_id": str(entity.id)}
            )

    # Contact-specific validation methods
    async def _check_duplicate_name(
        self,
        user_id: str,
        name: str,
        exclude_id: UUID | None = None
    ) -> None:
        """Check for duplicate contact name."""
        is_duplicate = await self.repository.check_duplicate_name(user_id, name, exclude_id)
        if is_duplicate:
            raise ContactAlreadyExistsError(
                detail=f"Contact '{name}' already exists",
                context={"name": name, "user_id": user_id}
            )

    async def _check_duplicate_email(
        self,
        user_id: str,
        email: str,
        exclude_id: UUID | None = None
    ) -> None:
        """Check for duplicate contact email."""
        is_duplicate = await self.repository.check_duplicate_email(user_id, email, exclude_id)
        if is_duplicate:
            raise DuplicateContactEmailError(
                detail=f"Contact with email '{email}' already exists",
                context={"email": email, "user_id": user_id}
            )

    async def _validate_contact_data(self, data: Dict[str, Any]) -> None:
        """Validate contact creation data."""
        if not data.get("name") or not data["name"].strip():
            raise ContactValidationError(
                detail="Contact name cannot be empty",
                context={"name": data.get("name")}
            )
        if len(data["name"].strip()) > MAX_CONTACT_NAME_LENGTH:
            raise ContactValidationError(
                detail="Contact name must be 100 characters or less",
                context={"name": data["name"], "length": len(data["name"])}
            )
        if data.get("email"):
            self._validate_email_format(data["email"])
        if data.get("phone"):
            self._validate_phone_format(data["phone"])
        if data.get("tax_number"):
            self._validate_tax_number_format(data["tax_number"])

    async def _validate_update_data(self, update_data: Dict[str, Any]) -> None:
        """Validate contact update data."""
        if "name" in update_data:
            if not update_data["name"] or not update_data["name"].strip():
                raise ContactValidationError(
                    detail="Contact name cannot be empty",
                    context={"name": update_data["name"]}
                )
        if "email" in update_data and update_data["email"]:
            self._validate_email_format(update_data["email"])
        if "phone" in update_data and update_data["phone"]:
            self._validate_phone_format(update_data["phone"])
        if "tax_number" in update_data and update_data["tax_number"]:
            self._validate_tax_number_format(update_data["tax_number"])

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
        phone_cleaned = re.sub(r'[^\d+\-\s\(\)]', '', phone.strip())
        if len(phone_cleaned) < 7 or len(phone_cleaned) > 20:
            raise InvalidContactPhoneError(
                detail="Phone number must be between 7 and 20 characters",
                context={"phone": phone, "cleaned_length": len(phone_cleaned)}
            )

    def _validate_tax_number_format(self, tax_number: str) -> None:
        """Validate tax number format."""
        tax_cleaned = re.sub(r'[^\w\-]', '', tax_number.strip())
        if len(tax_cleaned) < 5 or len(tax_cleaned) > 20:
            raise ContactTaxNumberError(
                detail="Tax number must be between 5 and 20 alphanumeric characters",
                context={"tax_number": tax_number, "cleaned_length": len(tax_cleaned)}
            )
