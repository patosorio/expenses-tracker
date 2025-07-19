from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select
import logging

from .models import Contact, ContactType
from .schemas import ContactResponse
from .exceptions import ContactNotFoundError

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
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating contact: {str(e)}")
            raise

    async def get_by_id(self, contact_id: UUID, user_id: str) -> Optional[Contact]:
        """Get contact by ID with user validation"""
        result = await self.db.execute(
            select(Contact).where(
                and_(Contact.id == contact_id, Contact.user_id == user_id, Contact.is_active == True)
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            logger.warning(f"Contact {contact_id} not found for user {user_id}")
            return None
            
        return contact

    async def update(self, contact: Contact) -> Contact:
        """Update contact in database"""
        try:
            await self.db.commit()
            await self.db.refresh(contact)
            logger.info(f"Updated contact {contact.id} for user {contact.user_id}")
            return contact
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating contact {contact.id}: {str(e)}")
            raise

    async def delete(self, contact: Contact) -> bool:
        """Soft delete contact"""
        try:
            contact.is_active = False
            await self.db.commit()
            logger.info(f"Soft deleted contact {contact.id} for user {contact.user_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting contact {contact.id}: {str(e)}")
            raise

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
        query = select(Contact).where(
            and_(Contact.user_id == user_id, Contact.is_active == True)
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
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Contact.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        contacts = result.scalars().all()
        
        return contacts, total_count

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
            and_(Contact.user_id == user_id, Contact.is_active == True)
        )
        
        if contact_type:
            query = query.where(Contact.contact_type == contact_type)
        
        query = query.order_by(Contact.name)
        result = await self.db.execute(query)
        results = result.all()
        
        return [
            {
                "id": row.id,
                "name": row.name,
                "contact_type": row.contact_type,
                "email": row.email,
                "phone": row.phone
            }
            for row in results
        ]

    async def check_duplicate_name(
        self,
        user_id: str,
        name: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if contact name already exists for the user"""
        query = select(Contact).where(
            and_(
                Contact.user_id == user_id,
                Contact.name == name,
                Contact.is_active == True
            )
        )
        
        if exclude_id:
            query = query.where(Contact.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def check_duplicate_email(
        self,
        user_id: str,
        email: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if contact email already exists for the user"""
        if not email:
            return False
            
        query = select(Contact).where(
            and_(
                Contact.user_id == user_id,
                Contact.email == email,
                Contact.is_active == True
            )
        )
        
        if exclude_id:
            query = query.where(Contact.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None 