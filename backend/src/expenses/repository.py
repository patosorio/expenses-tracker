from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, extract, desc, asc, case, select
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import logging

from .models import (
    Expense, DocumentAnalysis, ExpenseAttachment,
    ExpenseType, PaymentMethod, PaymentStatus, AnalysisStatus
)
from .schemas import ExpenseFilter, ExpenseStats, OverdueExpensesListResponse, OverdueExpenseResponse
from .exceptions import ExpenseNotFoundError, DocumentAnalysisNotFoundError, AttachmentNotFoundError

logger = logging.getLogger(__name__)


class ExpenseRepository:
    """Repository for expense data access operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # Core CRUD Operations
    async def create(self, expense: Expense) -> Expense:
        """Create expense in database"""
        try:
            self.db.add(expense)
            await self.db.commit()
            await self.db.refresh(expense)
            logger.info(f"Created expense {expense.id} for user {expense.user_id}")
            return expense
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating expense: {str(e)}")
            raise

    async def get_by_id(self, user_id: str, expense_id: uuid.UUID) -> Optional[Expense]:
        """Get expense by ID with full relationships"""
        result = await self.db.execute(
            select(Expense)
            .where(and_(Expense.id == expense_id, Expense.user_id == user_id, Expense.is_active == True))
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            logger.warning(f"Expense {expense_id} not found for user {user_id}")
            return None
            
        return expense

    async def update(self, expense: Expense) -> Expense:
        """Update expense in database"""
        try:
            expense.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(expense)
            logger.info(f"Updated expense {expense.id} for user {expense.user_id}")
            return expense
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating expense {expense.id}: {str(e)}")
            raise

    async def delete(self, expense: Expense) -> bool:
        """Soft delete expense"""
        try:
            expense.is_active = False
            expense.updated_at = datetime.utcnow()
            await self.db.commit()
            logger.info(f"Soft deleted expense {expense.id} for user {expense.user_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting expense {expense.id}: {str(e)}")
            raise

    # Filtering & Search Operations
    async def get_with_filters(
        self,
        user_id: str,
        filters: ExpenseFilter,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "expense_date",
        sort_order: str = "desc"
    ) -> Tuple[List[Expense], int]:
        """Get expenses with filtering and pagination"""
        query = self._build_base_query(user_id)
        query = self._apply_filters(query, filters)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(Expense, sort_by)))
        else:
            query = query.order_by(asc(getattr(Expense, sort_by)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        expenses = result.scalars().all()
        
        return expenses, total_count

    async def get_paginated(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "expense_date",
        sort_order: str = "desc"
    ) -> Tuple[List[Expense], int]:
        """Get paginated expenses without filters"""
        query = self._build_base_query(user_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(Expense, sort_by)))
        else:
            query = query.order_by(asc(getattr(Expense, sort_by)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        expenses = result.scalars().all()
        
        return expenses, total_count

    async def get_by_type(
        self,
        user_id: str,
        expense_type: ExpenseType,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Expense], int]:
        """Get expenses by type"""
        query = select(Expense).where(
            and_(
                Expense.user_id == user_id,
                Expense.expense_type == expense_type,
                Expense.is_active == True
            )
        )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        expenses = result.scalars().all()
        
        return expenses, total_count

    # Aggregation Operations
    async def get_stats(self, user_id: str) -> ExpenseStats:
        """Get expense statistics for dashboard"""
        # Get current month and last month dates
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Total expenses
        total_query = select(
            func.sum(Expense.total_amount).label('total_amount'),
            func.count(Expense.id).label('total_count')
        ).where(and_(Expense.user_id == user_id, Expense.is_active == True))
        total_result = await self.db.execute(total_query)
        total_row = total_result.first()
        
        # Pending payments
        pending_query = select(
            func.sum(Expense.total_amount).label('pending_amount')
        ).where(and_(
            Expense.user_id == user_id,
            Expense.payment_status == PaymentStatus.PENDING,
            Expense.is_active == True
        ))
        pending_result = await self.db.execute(pending_query)
        pending_row = pending_result.first()
        
        # Overdue invoices
        overdue_query = select(
            func.count(Expense.id).label('overdue_count'),
            func.sum(Expense.total_amount).label('overdue_amount')
        ).where(and_(
            Expense.user_id == user_id,
            Expense.expense_type == ExpenseType.INVOICE,
            Expense.payment_status == PaymentStatus.PENDING,
            Expense.payment_due_date < now,
            Expense.is_active == True
        ))
        overdue_result = await self.db.execute(overdue_query)
        overdue_row = overdue_result.first()
        
        # This month expenses
        this_month_query = select(
            func.sum(Expense.total_amount).label('this_month_amount')
        ).where(and_(
            Expense.user_id == user_id,
            Expense.expense_date >= current_month_start,
            Expense.is_active == True
        ))
        this_month_result = await self.db.execute(this_month_query)
        this_month_row = this_month_result.first()
        
        # Last month expenses
        last_month_query = select(
            func.sum(Expense.total_amount).label('last_month_amount')
        ).where(and_(
            Expense.user_id == user_id,
            Expense.expense_date >= last_month_start,
            Expense.expense_date < current_month_start,
            Expense.is_active == True
        ))
        last_month_result = await self.db.execute(last_month_query)
        last_month_row = last_month_result.first()
        
        # Top categories
        top_categories_query = select(
            Expense.category_id,
            func.sum(Expense.total_amount).label('total_amount'),
            func.count(Expense.id).label('count')
        ).where(and_(Expense.user_id == user_id, Expense.is_active == True)).group_by(
            Expense.category_id
        ).order_by(desc(func.sum(Expense.total_amount))).limit(5)
        top_categories_result = await self.db.execute(top_categories_query)
        top_categories = top_categories_result.all()
        
        # Top suppliers (contacts)
        top_suppliers_query = select(
            Expense.contact_id,
            func.sum(Expense.total_amount).label('total_amount'),
            func.count(Expense.id).label('count')
        ).where(and_(
            Expense.user_id == user_id,
            Expense.contact_id.isnot(None),
            Expense.is_active == True
        )).group_by(Expense.contact_id).order_by(
            desc(func.sum(Expense.total_amount))
        ).limit(5)
        top_suppliers_result = await self.db.execute(top_suppliers_query)
        top_suppliers = top_suppliers_result.all()
        
        # Calculate monthly change percentage
        this_month_total = this_month_row.this_month_amount or Decimal('0.00')
        last_month_total = last_month_row.last_month_amount or Decimal('0.00')
        
        if last_month_total > 0:
            monthly_change_percent = ((this_month_total - last_month_total) / last_month_total) * 100
        else:
            monthly_change_percent = Decimal('0.00')
        
        return ExpenseStats(
            total_expenses=total_row.total_amount or Decimal('0.00'),
            total_count=total_row.total_count or 0,
            pending_payments=pending_row.pending_amount or Decimal('0.00'),
            overdue_count=overdue_row.overdue_count or 0,
            overdue_amount=overdue_row.overdue_amount or Decimal('0.00'),
            this_month_total=this_month_total,
            last_month_total=last_month_total,
            monthly_change_percent=monthly_change_percent,
            top_categories=[{"category_id": str(cat.category_id), "total_amount": float(cat.total_amount), "count": cat.count} for cat in top_categories],
            top_suppliers=[{"contact_id": str(sup.contact_id), "total_amount": float(sup.total_amount), "count": sup.count} for sup in top_suppliers]
        )

    async def get_overdue_expenses(self, user_id: str) -> OverdueExpensesListResponse:
        """Get overdue invoices for tracking"""
        now = datetime.utcnow()
        
        query = select(Expense).where(
            and_(
                Expense.user_id == user_id,
                Expense.expense_type == ExpenseType.INVOICE,
                Expense.payment_status == PaymentStatus.PENDING,
                Expense.payment_due_date < now,
                Expense.is_active == True
            )
        ).order_by(Expense.payment_due_date)
        
        result = await self.db.execute(query)
        overdue_expenses = result.scalars().all()
        
        overdue_responses = []
        total_overdue_amount = Decimal('0.00')
        
        for expense in overdue_expenses:
            days_overdue = (now - expense.payment_due_date).days
            overdue_responses.append(OverdueExpenseResponse(
                id=expense.id,
                description=expense.description,
                contact_name=expense.contact.name if expense.contact else "Unknown",
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
            currency='EUR'  # Assuming EUR as default
        )

    # Document Analysis Operations
    async def create_document_analysis(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """Create document analysis"""
        try:
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
            logger.info(f"Created document analysis {analysis.id} for user {analysis.user_id}")
            return analysis
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating document analysis: {str(e)}")
            raise

    async def get_document_analysis_by_id(self, analysis_id: uuid.UUID) -> Optional[DocumentAnalysis]:
        """Get document analysis by ID"""
        result = await self.db.execute(
            select(DocumentAnalysis).where(DocumentAnalysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            logger.warning(f"Document analysis {analysis_id} not found")
            return None
            
        return analysis

    async def update_document_analysis(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """Update document analysis"""
        try:
            analysis.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(analysis)
            logger.info(f"Updated document analysis {analysis.id}")
            return analysis
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating document analysis {analysis.id}: {str(e)}")
            raise

    # Attachment Operations
    async def create_attachment(self, attachment: ExpenseAttachment) -> ExpenseAttachment:
        """Create expense attachment"""
        try:
            self.db.add(attachment)
            await self.db.commit()
            await self.db.refresh(attachment)
            logger.info(f"Created attachment {attachment.id} for expense {attachment.expense_id}")
            return attachment
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating attachment: {str(e)}")
            raise

    async def get_attachment_by_id(self, attachment_id: uuid.UUID) -> Optional[ExpenseAttachment]:
        """Get attachment by ID"""
        result = await self.db.execute(
            select(ExpenseAttachment).where(ExpenseAttachment.id == attachment_id)
        )
        attachment = result.scalar_one_or_none()
        
        if not attachment:
            logger.warning(f"Attachment {attachment_id} not found")
            return None
            
        return attachment

    async def delete_attachment(self, attachment: ExpenseAttachment) -> bool:
        """Delete attachment"""
        try:
            await self.db.delete(attachment)
            await self.db.commit()
            logger.info(f"Deleted attachment {attachment.id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting attachment {attachment.id}: {str(e)}")
            raise

    # Private helper methods
    def _build_base_query(self, user_id: str):
        """Build base query for user expenses"""
        return select(Expense).where(
            and_(Expense.user_id == user_id, Expense.is_active == True)
        )

    def _apply_filters(self, query, filters: ExpenseFilter):
        """Apply filters to query"""
        if filters.expense_type:
            query = query.where(Expense.expense_type == filters.expense_type)
        
        if filters.payment_status:
            query = query.where(Expense.payment_status == filters.payment_status)
        
        if filters.payment_method:
            query = query.where(Expense.payment_method == filters.payment_method)
        
        if filters.category_id:
            query = query.where(Expense.category_id == filters.category_id)
        
        if filters.contact_id:
            query = query.where(Expense.contact_id == filters.contact_id)
        
        if filters.min_amount:
            query = query.where(Expense.total_amount >= filters.min_amount)
        
        if filters.max_amount:
            query = query.where(Expense.total_amount <= filters.max_amount)
        
        if filters.date_from:
            query = query.where(Expense.expense_date >= filters.date_from)
        
        if filters.date_to:
            query = query.where(Expense.expense_date <= filters.date_to)
        
        if filters.overdue_only:
            now = datetime.utcnow()
            query = query.where(and_(
                Expense.expense_type == ExpenseType.invoice,
                Expense.payment_status == PaymentStatus.PENDING,
                Expense.payment_due_date < now
            ))
        
        if filters.tags:
            # Filter by tags (assuming tags is a JSON array)
            for tag in filters.tags:
                query = query.where(Expense.tags.contains([tag]))
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(or_(
                Expense.description.ilike(search_term),
                Expense.notes.ilike(search_term),
                Expense.invoice_number.ilike(search_term)
            ))
        
        return query 