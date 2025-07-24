from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select, text
from typing import List, Tuple
from uuid import UUID
import logging

from .models import Contact, ContactType
from ..core.shared.base_repository import BaseRepository
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class ContactRepository(BaseRepository[Contact]):
    """Repository for contact data access operations extending BaseRepository."""
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Contact)

    # Business-specific methods
    async def get_by_email(self, user_id: str, email: str) -> Contact | None:
        try:
            query = self._build_base_query(user_id)
            query = query.where(func.lower(Contact.email) == email.lower())
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error getting contact by email: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking contact email",
                context={"user_id": user_id, "email": email}
            )

    async def get_contacts_summary(
        self,
        user_id: str,
        contact_type: ContactType | None = None
    ) -> List[dict]:
        try:
            query = select(
                Contact.id,
                Contact.name,
                Contact.contact_type,
                Contact.email,
                Contact.phone
            ).where(
                and_(Contact.user_id == user_id, Contact.is_active.is_(True))
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
        except Exception as e:
            logger.error(f"Database error getting contacts summary for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving contacts summary",
                context={"user_id": user_id}
            )

    async def check_duplicate_name(
        self,
        user_id: str,
        name: str,
        exclude_id: UUID | None = None
    ) -> bool:
        try:
            query = select(Contact).where(
                and_(
                    Contact.user_id == user_id,
                    func.lower(Contact.name) == func.lower(name.strip()),
                    Contact.is_active.is_(True)
                )
            )
            if exclude_id:
                query = query.where(Contact.id != exclude_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Database error checking duplicate contact name: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking duplicate contact name",
                context={"name": name, "user_id": user_id}
            )

    async def check_duplicate_email(
        self,
        user_id: str,
        email: str,
        exclude_id: UUID | None = None
    ) -> bool:
        try:
            if not email or not email.strip():
                return False
            query = select(Contact).where(
                and_(
                    Contact.user_id == user_id,
                    func.lower(Contact.email) == func.lower(email.strip()),
                    Contact.is_active.is_(True)
                )
            )
            if exclude_id:
                query = query.where(Contact.id != exclude_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Database error checking duplicate contact email: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking duplicate email",
                context={"email": email, "user_id": user_id}
            )

    async def is_contact_in_use(self, contact_id: UUID) -> bool:
        try:
            expense_check = await self.db.execute(text("""
                SELECT 1 FROM expenses 
                WHERE contact_id = :contact_id AND is_active = true 
                LIMIT 1
            """), {"contact_id": str(contact_id)})
            if expense_check.fetchone():
                return True
            try:
                invoice_check = await self.db.execute(text("""
                    SELECT 1 FROM invoices 
                    WHERE contact_id = :contact_id AND is_active = true 
                    LIMIT 1
                """), {"contact_id": str(contact_id)})
                if invoice_check.fetchone():
                    return True
            except Exception:
                pass
            return False
        except Exception as e:
            logger.error(f"Database error checking contact usage: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking contact usage",
                context={"contact_id": str(contact_id)}
            )

    async def get_contacts_by_type(
        self,
        user_id: str,
        contact_type: ContactType,
        include_inactive: bool = False
    ) -> List[Contact]:
        try:
            query = select(Contact).where(
                and_(
                    Contact.user_id == user_id,
                    Contact.contact_type == contact_type
                )
            )
            if not include_inactive:
                query = query.where(Contact.is_active.is_(True))
            query = query.order_by(Contact.name)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Database error getting contacts by type {contact_type}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving contacts by type",
                context={"contact_type": contact_type.value, "user_id": user_id}
            )

    async def search_contacts(
        self,
        user_id: str,
        search_term: str,
        limit: int = 10
    ) -> List[Contact]:
        try:
            if not search_term or len(search_term.strip()) < 2:
                return []
            search_pattern = f"%{search_term.strip()}%"
            query = select(Contact).where(
                and_(
                    Contact.user_id == user_id,
                    Contact.is_active.is_(True),
                    or_(
                        Contact.name.ilike(search_pattern),
                        Contact.email.ilike(search_pattern),
                        Contact.phone.ilike(search_pattern)
                    )
                )
            ).order_by(Contact.name).limit(limit)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Database error searching contacts: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while searching contacts",
                context={"search_term": search_term, "user_id": user_id}
            )