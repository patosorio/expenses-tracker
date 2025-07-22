from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func, select, text
import logging

from .models import Contact, ContactType
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class ContactRepository:
    """Repository for contact data access operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # Core CRUD Operations
    async def create(self, contact: Contact) -> Contact:
        """Create contact in database"""
        try:
            self.db.add(contact)
            await self.db.commit()
            await self.db.refresh(contact)
            logger.info(f"Created contact {contact.id} for user {contact.user_id}")
            return contact
        
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating contact: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while creating contact",
                context={"user_id": contact.user_id, "original_error": str(e)}
            )
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating contact: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while creating contact",
                context={"user_id": contact.user_id, "original_error": str(e)}
            )

    async def get_by_id(self, contact_id: UUID, user_id: str) -> Optional[Contact]:
        """Get contact by ID with user validation"""
        try:
            result = await self.db.execute(
                select(Contact).where(
                    and_(
                        Contact.id == contact_id,
                        Contact.user_id == user_id,
                        Contact.is_active == True
                    )
                )
            )
            contact = result.scalar_one_or_none()

            if not contact:
                logger.debug(f"Contact {contact_id} not found for user {user_id}")

            return contact
        
        except SQLAlchemyError as e: 
            logger.error(f"Database error retrieving contact {contact_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving contact",
                context={"contact_id": str(contact_id), "user_id": user_id, "original_error": str(e)}
            )

    async def update(self, contact: Contact) -> Contact:
        """Update contact in database"""
        try:
            await self.db.commit()
            await self.db.refresh(contact)
            logger.info(f"Updated contact {contact.id} for user {contact.user_id}")
            return contact
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating contact {contact.id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while updating contact",
                context={"contact_id": str(contact.id), "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error updating contact {contact.id}: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while updating contact",
                context={"contact_id": str(contact.id), "original_error": str(e)}
            )

    async def delete(self, contact: Contact) -> bool:
        """Soft delete contact"""
        try:
            contact.is_active = False
            await self.db.commit()
            logger.info(f"Soft deleted contact {contact.id} for user {contact.user_id}")
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error deleting contact {contact.id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while deleting contact",
                context={"contact_id": str(contact.id), "original_error": str(e)}
            )

    # Query Operations
    async def get_contacts(
        self,
        user_id: str,
        contact_type: Optional[ContactType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Contact], int]:
        """Get contacts with filtering and pagination"""
        # Build base query
        try:
            query = select(Contact).where(
                and_(Contact.user_id == user_id, Contact.is_active == True)
            )
            
            if contact_type:
                query = query.where(Contact.contact_type == contact_type)
            
            if search:
                search_term = f"%{search.strip()}%"
                query = query.where(
                    or_(
                        Contact.name.ilike(search_term),
                        Contact.email.ilike(search_term),
                        Contact.tax_number.ilike(search_term),
                        Contact.phone.ilike(search_term)
                    )
                )
        
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total_count = total_result.scalar()
            
            # Get paginated results
            query = query.order_by(Contact.name).offset(skip).limit(limit)
            result = await self.db.execute(query)
            contacts = list(result.scalars().all())
            
            return contacts, total_count
    
        except SQLAlchemyError as e:
                logger.error(f"Database error getting contacts for user {user_id}: {str(e)}")
                raise InternalServerError(
                    detail="Database error occurred while retrieving contacts",
                    context={"user_id": user_id, "original_error": str(e)}
                )

    async def get_contacts_summary(
        self,
        user_id: str,
        contact_type: Optional[ContactType] = None
    ) -> List[dict]:
        """Get lightweight contact summary for dropdowns"""
        try:
            query = select(
                Contact.id,
                Contact.name,
                Contact.contact_type,
                Contact.email,
                Contact.phone
            ).where(
                and_(Contact.user_id == user_id, Contact.is_active == True)
            )
            
            if contact_type:
                query = query.where(Contact.contact_type == contact_type)
            
            query = query.order_by(Contact.name)
            result = await self.db.execute(query)
            results = result.all()
            
            return [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "contact_type": row.contact_type.value if row.contact_type else None,
                    "email": row.email,
                    "phone": row.phone
                }
                for row in results
            ]
        
        except SQLAlchemyError as e:
            logger.error(f"Database error getting contacts summary for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving contacts summary",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def check_duplicate_name(
        self,
        user_id: str,
        name: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if contact name already exists for the user"""
        try:
            query = select(Contact).where(
                and_(
                    Contact.user_id == user_id,
                    func.lower(Contact.name) == func.lower(name.strip()),
                    Contact.is_active == True
                )
            )
            
            if exclude_id:
                query = query.where(Contact.id != exclude_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        
        except SQLAlchemyError as e:
            logger.error(f"Database error checking duplicate contact name: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking duplicate contact name",
                context={"name": name, "user_id": user_id, "original_error": str(e)}
            )

    async def check_duplicate_email(
        self,
        user_id: str,
        email: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if contact email already exists for the user."""
        try:
            if not email or not email.strip():
                return False
                
            query = select(Contact).where(
                and_(
                    Contact.user_id == user_id,
                    func.lower(Contact.email) == func.lower(email.strip()),
                    Contact.is_active == True
                )
            )
            
            if exclude_id:
                query = query.where(Contact.id != exclude_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking duplicate contact email: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking duplicate email",
                context={"email": email, "user_id": user_id, "original_error": str(e)}
            )

    # Business logic support methods

    async def is_contact_in_use(self, contact_id: UUID) -> bool:
        """Check if contact is being used in expenses or invoices."""
        try:
            # Check if contact has any expenses (assuming expenses table exists)
            expense_check = await self.db.execute(text("""
                SELECT 1 FROM expenses 
                WHERE contact_id = :contact_id AND is_active = true 
                LIMIT 1
            """), {"contact_id": str(contact_id)})
            
            if expense_check.fetchone():
                return True
            
            # Check if contact has any invoices (if invoices table exists)
            try:
                invoice_check = await self.db.execute(text("""
                    SELECT 1 FROM invoices 
                    WHERE contact_id = :contact_id AND is_active = true 
                    LIMIT 1
                """), {"contact_id": str(contact_id)})
                
                if invoice_check.fetchone():
                    return True
            except SQLAlchemyError:
                # Invoices table might not exist yet, ignore
                pass
            
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking contact usage: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking contact usage",
                context={"contact_id": str(contact_id), "original_error": str(e)}
            )

    async def get_contacts_by_type(
        self,
        user_id: str,
        contact_type: ContactType,
        include_inactive: bool = False
    ) -> List[Contact]:
        """Get all contacts of a specific type."""
        try:
            query = select(Contact).where(
                and_(
                    Contact.user_id == user_id,
                    Contact.contact_type == contact_type
                )
            )
            
            if not include_inactive:
                query = query.where(Contact.is_active == True)
                
            query = query.order_by(Contact.name)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting contacts by type {contact_type}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving contacts by type",
                context={"contact_type": contact_type.value, "user_id": user_id, "original_error": str(e)}
            )

    async def search_contacts(
        self,
        user_id: str,
        search_term: str,
        limit: int = 10
    ) -> List[Contact]:
        """Search contacts for autocomplete functionality."""
        try:
            if not search_term or len(search_term.strip()) < 2:
                return []
                
            search_pattern = f"%{search_term.strip()}%"
            
            query = select(Contact).where(
                and_(
                    Contact.user_id == user_id,
                    Contact.is_active == True,
                    or_(
                        Contact.name.ilike(search_pattern),
                        Contact.email.ilike(search_pattern),
                        Contact.phone.ilike(search_pattern)
                    )
                )
            ).order_by(Contact.name).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error(f"Database error searching contacts: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while searching contacts",
                context={"search_term": search_term, "user_id": user_id, "original_error": str(e)}
            )