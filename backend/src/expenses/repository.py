from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc, case, select
from typing import List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import logging

from .models import (
    Expense, DocumentAnalysis, ExpenseAttachment,
    ExpenseType, PaymentStatus
)
from .schemas import ExpenseFilter, ExpenseStats, OverdueExpensesListResponse, OverdueExpenseResponse
from ..core.shared.base_repository import BaseRepository
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class ExpenseRepository(BaseRepository[Expense]):
    """Repository for expense data access operations extending BaseRepository."""
    def __init__(self, db: AsyncSession) -> None:
        """Initialize ExpenseRepository with database session."""
        super().__init__(db, Expense)

    async def check_duplicate_invoice_number(
        self,
        user_id: str,
        invoice_number: str,
        exclude_id: uuid.UUID | None = None
    ) -> bool:
        """Check if invoice number already exists for the user."""
        try:
            if not invoice_number or not invoice_number.strip():
                return False
            query = select(Expense).where(
                and_(
                    Expense.user_id == user_id,
                    func.lower(Expense.invoice_number) == func.lower(invoice_number.strip()),
                    Expense.is_active.is_(True)
                )
            )
            if exclude_id:
                query = query.where(Expense.id != exclude_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Database error checking duplicate invoice number: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while checking duplicate invoice number",
                context={"invoice_number": invoice_number, "user_id": user_id}
            )

    async def get_stats(self, user_id: str) -> ExpenseStats:
        """Get expense statistics for dashboard with optimized queries."""
        try:
            now = datetime.utcnow()
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            stats_query = select(
                func.sum(Expense.total_amount).label('total_amount'),
                func.count(Expense.id).label('total_count'),
                func.sum(case((Expense.payment_status == PaymentStatus.PENDING, Expense.total_amount), else_=0)).label('pending_amount'),
                func.sum(case(
                    (and_(
                        Expense.expense_type == ExpenseType.INVOICE,
                        Expense.payment_status == PaymentStatus.PENDING,
                        Expense.payment_due_date < now
                    ), Expense.total_amount), else_=0)).label('overdue_amount'),
                func.count(case(
                    (and_(
                        Expense.expense_type == ExpenseType.INVOICE,
                        Expense.payment_status == PaymentStatus.PENDING,
                        Expense.payment_due_date < now
                    ), 1), else_=None)).label('overdue_count'),
                func.sum(case((Expense.expense_date >= current_month_start, Expense.total_amount), else_=0)).label('this_month_amount'),
                func.sum(case(
                    (and_(
                        Expense.expense_date >= last_month_start,
                        Expense.expense_date < current_month_start
                    ), Expense.total_amount), else_=0)).label('last_month_amount')
            ).where(and_(Expense.user_id == user_id, Expense.is_active.is_(True)))
            stats_result = await self.db.execute(stats_query)
            stats = stats_result.first()
            this_month_total = stats.this_month_amount or Decimal('0.00')
            last_month_total = stats.last_month_amount or Decimal('0.00')
            if last_month_total > 0:
                monthly_change_percent = ((this_month_total - last_month_total) / last_month_total) * 100
            else:
                monthly_change_percent = Decimal('0.00') if this_month_total == 0 else Decimal('100.00')
            top_categories = await self._get_top_categories(user_id)
            top_suppliers = await self._get_top_suppliers(user_id)
            return ExpenseStats(
                total_expenses=stats.total_amount or Decimal('0.00'),
                total_count=stats.total_count or 0,
                pending_payments=stats.pending_amount or Decimal('0.00'),
                overdue_count=stats.overdue_count or 0,
                overdue_amount=stats.overdue_amount or Decimal('0.00'),
                this_month_total=this_month_total,
                last_month_total=last_month_total,
                monthly_change_percent=monthly_change_percent,
                top_categories=top_categories,
                top_suppliers=top_suppliers
            )
        except Exception as e:
            logger.error(f"Database error getting stats for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving expense statistics",
                context={"user_id": user_id}
            )

    async def get_overdue_expenses(self, user_id: str) -> OverdueExpensesListResponse:
        """Get overdue invoices for tracking with proper error handling."""
        try:
            now = datetime.utcnow()
            query = select(Expense).where(
                and_(
                    Expense.user_id == user_id,
                    Expense.expense_type == ExpenseType.INVOICE,
                    Expense.payment_status == PaymentStatus.PENDING,
                    Expense.payment_due_date < now,
                    Expense.is_active.is_(True)
                )
            ).order_by(Expense.payment_due_date)
            result = await self.db.execute(query)
            overdue_expenses = list(result.scalars().all())
            overdue_responses = []
            total_overdue_amount = Decimal('0.00')
            for expense in overdue_expenses:
                days_overdue = (now - expense.payment_due_date).days
                contact_name = "Unknown"
                try:
                    if expense.contact:
                        contact_name = expense.contact.name
                except Exception as e:
                    logger.warning(f"Could not load contact for expense {expense.id}: {e!s}")
                overdue_responses.append(OverdueExpenseResponse(
                    id=expense.id,
                    description=expense.description,
                    contact_name=contact_name,
                    invoice_number=expense.invoice_number,
                    total_amount=expense.total_amount,
                    payment_due_date=expense.payment_due_date,
                    days_overdue=days_overdue,
                    currency=expense.currency
                ))
                total_overdue_amount += expense.total_amount
            return OverdueExpensesListResponse(
                overdue_invoices=overdue_responses,
                total_overdue_amount=total_overdue_amount,
                count=len(overdue_responses),
                currency='USD'
            )
        except Exception as e:
            logger.error(f"Database error getting overdue expenses for user {user_id}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving overdue expenses",
                context={"user_id": user_id}
            )

    async def create_document_analysis(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """Create document analysis with proper error handling."""
        try:
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
            logger.info(f"Created document analysis {analysis.id} for user {analysis.user_id}")
            return analysis
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Database error creating document analysis: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while creating document analysis",
                context={"user_id": analysis.user_id}
            )

    async def get_document_analysis_by_id(self, analysis_id: uuid.UUID) -> DocumentAnalysis | None:
        """Get document analysis by ID with proper error handling."""
        try:
            result = await self.db.execute(
                select(DocumentAnalysis).where(DocumentAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            if not analysis:
                logger.debug(f"Document analysis {analysis_id} not found")
            return analysis
        except Exception as e:
            logger.error(f"Database error retrieving document analysis {analysis_id}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while retrieving document analysis",
                context={"analysis_id": str(analysis_id)}
            )

    async def update_document_analysis(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """Update document analysis with proper error handling."""
        try:
            analysis.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(analysis)
            logger.info(f"Updated document analysis {analysis.id}")
            return analysis
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Database error updating document analysis {analysis.id}: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while updating document analysis",
                context={"analysis_id": str(analysis.id)}
            )

    async def create_attachment(self, attachment: ExpenseAttachment) -> ExpenseAttachment:
        """Create expense attachment with proper error handling."""
        try:
            self.db.add(attachment)
            await self.db.commit()
            await self.db.refresh(attachment)
            logger.info(f"Created attachment {attachment.id} for expense {attachment.expense_id}")
            return attachment
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Database error creating attachment: {e!s}")
            raise InternalServerError(
                detail="Database error occurred while creating attachment",
                context={"expense_id": str(attachment.expense_id)}
            )

    # Private helper methods
    async def _get_top_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get top categories by total amount."""
        try:
            top_categories_query = select(
                Expense.category_id,
                func.sum(Expense.total_amount).label('total_amount'),
                func.count(Expense.id).label('count')
            ).where(
                and_(Expense.user_id == user_id, Expense.is_active.is_(True))
            ).group_by(
                Expense.category_id
            ).order_by(desc(func.sum(Expense.total_amount))).limit(5)
            result = await self.db.execute(top_categories_query)
            top_categories = result.all()
            return [
                {
                    "category_id": str(cat.category_id), 
                    "total_amount": float(cat.total_amount), 
                    "count": cat.count
                } for cat in top_categories
            ]
        except Exception as e:
            logger.error(f"Error getting top categories: {e!s}")
            return []

    async def _get_top_suppliers(self, user_id: str) -> List[Dict[str, Any]]:
        """Get top suppliers by total amount."""
        try:
            top_suppliers_query = select(
                Expense.contact_id,
                func.sum(Expense.total_amount).label('total_amount'),
                func.count(Expense.id).label('count')
            ).where(and_(
                Expense.user_id == user_id,
                Expense.contact_id.isnot(None),
                Expense.is_active.is_(True)
            )).group_by(Expense.contact_id).order_by(
                desc(func.sum(Expense.total_amount))
            ).limit(5)
            result = await self.db.execute(top_suppliers_query)
            top_suppliers = result.all()
            return [
                {
                    "contact_id": str(sup.contact_id), 
                    "total_amount": float(sup.total_amount), 
                    "count": sup.count
                } for sup in top_suppliers
            ]
        except Exception as e:
            logger.error(f"Error getting top suppliers: {e!s}")
            return []