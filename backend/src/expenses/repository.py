from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, extract, desc, asc, case, select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
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
from ..core.shared.exceptions import InternalServerError

logger = logging.getLogger(__name__)


class ExpenseRepository:
    """Repository for expense data access operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # Core CRUD Operations
    async def create(self, expense: Expense) -> Expense:
        """Create expense in database with proper error handling."""
        try:
            self.db.add(expense)
            await self.db.commit()
            await self.db.refresh(expense)
            logger.info(f"Created expense {expense.id} for user {expense.user_id}")
            return expense
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating expense: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while creating expense",
                context={"user_id": expense.user_id, "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating expense: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while creating expense",
                context={"user_id": expense.user_id, "original_error": str(e)}
            )

    async def get_by_id(self, user_id: str, expense_id: uuid.UUID) -> Optional[Expense]:
        """Get expense by ID with full relationships and proper error handling."""
        try:
            result = await self.db.execute(
                select(Expense)
                .options(
                    selectinload(Expense.attachments),
                    selectinload(Expense.document_analysis),
                    selectinload(Expense.category),
                    selectinload(Expense.contact),
                    selectinload(Expense.tax_config)
                )
                .where(and_(
                    Expense.id == expense_id, 
                    Expense.user_id == user_id, 
                    Expense.is_active == True
                ))
            )
            expense = result.scalar_one_or_none()
            
            if not expense:
                logger.debug(f"Expense {expense_id} not found for user {user_id}")
                
            return expense
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving expense {expense_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving expense",
                context={"expense_id": str(expense_id), "user_id": user_id, "original_error": str(e)}
            )

    async def update(self, expense: Expense) -> Expense:
        """Update expense in database with proper error handling."""
        try:
            expense.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(expense)
            logger.info(f"Updated expense {expense.id} for user {expense.user_id}")
            return expense
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating expense {expense.id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while updating expense",
                context={"expense_id": str(expense.id), "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error updating expense {expense.id}: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while updating expense",
                context={"expense_id": str(expense.id), "original_error": str(e)}
            )

    async def delete(self, expense: Expense) -> bool:
        """Soft delete expense with proper error handling."""
        try:
            expense.is_active = False
            expense.updated_at = datetime.utcnow()
            await self.db.commit()
            logger.info(f"Soft deleted expense {expense.id} for user {expense.user_id}")
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error deleting expense {expense.id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while deleting expense",
                context={"expense_id": str(expense.id), "original_error": str(e)}
            )

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
        """Get expenses with filtering and pagination - optimized."""
        try:
            query = self._build_base_query(user_id)
            query = self._apply_filters(query, filters)
            
            # Get total count efficiently
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total_count = total_result.scalar()
            
            # Apply sorting with proper column validation
            sort_column = getattr(Expense, sort_by, Expense.expense_date)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            result = await self.db.execute(query)
            expenses = list(result.scalars().all())
            
            return expenses, total_count
        except SQLAlchemyError as e:
            logger.error(f"Database error getting expenses with filters for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving expenses",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_paginated(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "expense_date",
        sort_order: str = "desc"
    ) -> Tuple[List[Expense], int]:
        """Get paginated expenses without filters - optimized."""
        try:
            query = self._build_base_query(user_id)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total_count = total_result.scalar()
            
            # Apply sorting with proper column validation
            sort_column = getattr(Expense, sort_by, Expense.expense_date)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            result = await self.db.execute(query)
            expenses = list(result.scalars().all())
            
            return expenses, total_count
        except SQLAlchemyError as e:
            logger.error(f"Database error getting paginated expenses for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving expenses",
                context={"user_id": user_id, "original_error": str(e)}
            )

    async def get_by_type(
        self,
        user_id: str,
        expense_type: ExpenseType,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Expense], int]:
        """Get expenses by type with proper error handling."""
        try:
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
            
            # Apply pagination and ordering
            query = (query
                    .order_by(desc(Expense.expense_date))
                    .offset(skip)
                    .limit(limit))
                    
            result = await self.db.execute(query)
            expenses = list(result.scalars().all())
            
            return expenses, total_count
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {expense_type} expenses for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail=f"Database error occurred while retrieving {expense_type.value} expenses",
                context={"user_id": user_id, "expense_type": expense_type.value, "original_error": str(e)}
            )

    # Business logic support methods
    async def check_duplicate_invoice_number(
        self,
        user_id: str,
        invoice_number: str,
        exclude_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if invoice number already exists for the user."""
        try:
            if not invoice_number or not invoice_number.strip():
                return False
                
            query = select(Expense).where(
                and_(
                    Expense.user_id == user_id,
                    func.lower(Expense.invoice_number) == func.lower(invoice_number.strip()),
                    Expense.is_active == True
                )
            )
            
            if exclude_id:
                query = query.where(Expense.id != exclude_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error checking duplicate invoice number: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while checking duplicate invoice number",
                context={"invoice_number": invoice_number, "user_id": user_id, "original_error": str(e)}
            )

    # Aggregation Operations
    async def get_stats(self, user_id: str) -> ExpenseStats:
        """Get expense statistics for dashboard with optimized queries."""
        try:
            # Get current month and last month dates
            now = datetime.utcnow()
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            
            # Use optimized single query approach with conditional aggregates
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
            ).where(and_(Expense.user_id == user_id, Expense.is_active == True))
            
            stats_result = await self.db.execute(stats_query)
            stats = stats_result.first()
            
            # Calculate monthly change percentage
            this_month_total = stats.this_month_amount or Decimal('0.00')
            last_month_total = stats.last_month_amount or Decimal('0.00')
            
            if last_month_total > 0:
                monthly_change_percent = ((this_month_total - last_month_total) / last_month_total) * 100
            else:
                monthly_change_percent = Decimal('0.00') if this_month_total == 0 else Decimal('100.00')
            
            # Get top categories
            top_categories = await self._get_top_categories(user_id)
            
            # Get top suppliers
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
        except SQLAlchemyError as e:
            logger.error(f"Database error getting stats for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving expense statistics",
                context={"user_id": user_id, "original_error": str(e)}
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
                    Expense.is_active == True
                )
            ).order_by(Expense.payment_due_date)
            
            result = await self.db.execute(query)
            overdue_expenses = list(result.scalars().all())
            
            overdue_responses = []
            total_overdue_amount = Decimal('0.00')
            
            for expense in overdue_expenses:
                days_overdue = (now - expense.payment_due_date).days
                contact_name = "Unknown"
                
                # Safely get contact name
                try:
                    if expense.contact:
                        contact_name = expense.contact.name
                except Exception as e:
                    logger.warning(f"Could not load contact for expense {expense.id}: {str(e)}")
                
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
                currency='USD'  # Default currency
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting overdue expenses for user {user_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving overdue expenses",
                context={"user_id": user_id, "original_error": str(e)}
            )

    # Document Analysis Operations
    async def create_document_analysis(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """Create document analysis with proper error handling."""
        try:
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
            logger.info(f"Created document analysis {analysis.id} for user {analysis.user_id}")
            return analysis
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating document analysis: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while creating document analysis",
                context={"user_id": analysis.user_id, "original_error": str(e)}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating document analysis: {str(e)}")
            raise InternalServerError(
                detail="Unexpected error occurred while creating document analysis",
                context={"user_id": analysis.user_id, "original_error": str(e)}
            )

    async def get_document_analysis_by_id(self, analysis_id: uuid.UUID) -> Optional[DocumentAnalysis]:
        """Get document analysis by ID with proper error handling."""
        try:
            result = await self.db.execute(
                select(DocumentAnalysis).where(DocumentAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                logger.debug(f"Document analysis {analysis_id} not found")
                
            return analysis
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving document analysis {analysis_id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while retrieving document analysis",
                context={"analysis_id": str(analysis_id), "original_error": str(e)}
            )

    async def update_document_analysis(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """Update document analysis with proper error handling."""
        try:
            analysis.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(analysis)
            logger.info(f"Updated document analysis {analysis.id}")
            return analysis
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating document analysis {analysis.id}: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while updating document analysis",
                context={"analysis_id": str(analysis.id), "original_error": str(e)}
            )

    # Attachment Operations
    async def create_attachment(self, attachment: ExpenseAttachment) -> ExpenseAttachment:
        """Create expense attachment with proper error handling."""
        try:
            self.db.add(attachment)
            await self.db.commit()
            await self.db.refresh(attachment)
            logger.info(f"Created attachment {attachment.id} for expense {attachment.expense_id}")
            return attachment
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating attachment: {str(e)}")
            raise InternalServerError(
                detail="Database error occurred while creating attachment",
                context={"expense_id": str(attachment.expense_id), "original_error": str(e)}
            )

    # Private helper methods
    def _build_base_query(self, user_id: str):
        """Build base query for user expenses."""
        return select(Expense).where(
            and_(Expense.user_id == user_id, Expense.is_active == True)
        )

    def _apply_filters(self, query, filters: ExpenseFilter):
        """Apply filters to query with proper validation."""
        if filters.expense_type:
            query = query.where(Expense.expense_type == filters.expense_type)
        
        if filters.payment_status:
            query = query.where(Expense.payment_status == filters.payment_status)
        
        if filters.payment_method:
            query = query.where(Expense.payment_method == filters.payment_method)
        
        if filters.category_id:
            query = query.where(Expense.category_id == filters.category_id)
        
        if hasattr(filters, 'contact_id') and filters.contact_id:
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
                Expense.expense_type == ExpenseType.INVOICE,
                Expense.payment_status == PaymentStatus.PENDING,
                Expense.payment_due_date < now
            ))
        
        if hasattr(filters, 'tags') and filters.tags:
            # Filter by tags (assuming tags is a JSON array)
            for tag in filters.tags:
                query = query.where(Expense.tags.contains([tag]))
        
        if filters.search:
            search_term = f"%{filters.search.strip()}%"
            query = query.where(or_(
                Expense.description.ilike(search_term),
                Expense.notes.ilike(search_term),
                Expense.invoice_number.ilike(search_term)
            ))
        
        return query

    async def _get_top_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get top categories by total amount."""
        try:
            top_categories_query = select(
                Expense.category_id,
                func.sum(Expense.total_amount).label('total_amount'),
                func.count(Expense.id).label('count')
            ).where(
                and_(Expense.user_id == user_id, Expense.is_active == True)
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
        except SQLAlchemyError as e:
            logger.error(f"Error getting top categories: {str(e)}")
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
                Expense.is_active == True
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
        except SQLAlchemyError as e:
            logger.error(f"Error getting top suppliers: {str(e)}")
            return []