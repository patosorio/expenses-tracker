from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from .service import ExpenseService
from .schemas import (
    SimpleExpenseCreate, InvoiceExpenseCreate, ExpenseUpdate,
    ExpenseFilter,
    ExpenseResponse, ExpenseCreateResponse, ExpenseListResponse, ExpenseListPaginatedResponse,
    OverdueExpensesListResponse, ExpenseStats
)
from .models import ExpenseType, PaymentMethod, PaymentStatus
from ..auth.dependencies import get_current_user
from ..users.models import User
from ..core.database import get_db
from ..core.shared.decorators import api_endpoint
from ..core.shared.pagination import create_legacy_expense_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/simple", response_model=ExpenseCreateResponse, status_code=201)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def create_simple_expense(
    expense_data: SimpleExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a simple (receipt) expense with comprehensive validation."""
    service = ExpenseService(db)
    expense = await service.create_simple_expense(current_user.id, expense_data)
    return ExpenseCreateResponse.model_validate(expense)


@router.post("/invoice", response_model=ExpenseCreateResponse, status_code=201)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def create_invoice_expense(
    expense_data: InvoiceExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an invoice expense with tax calculations and validation."""
    service = ExpenseService(db)
    expense = await service.create_invoice_expense(current_user.id, expense_data)
    return ExpenseCreateResponse.model_validate(expense)


@router.get("/", response_model=ExpenseListPaginatedResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_expenses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    expense_type: Optional[ExpenseType] = Query(None, description="Filter by expense type"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum amount filter"),
    date_from: Optional[datetime] = Query(None, description="Filter expenses from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter expenses up to this date"),
    overdue_only: bool = Query(False, description="Show only overdue invoices"),
    search: Optional[str] = Query(None, description="Search in description, notes, or invoice number"),
    sort_by: str = Query("expense_date", regex="^(expense_date|total_amount|description)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expenses with advanced filtering and pagination."""
    service = ExpenseService(db)
    filters = {}
    if expense_type:
        filters['expense_type'] = expense_type
    if payment_status:
        filters['payment_status'] = payment_status
    if payment_method:
        filters['payment_method'] = payment_method
    if category_id:
        filters['category_id'] = category_id
    if min_amount is not None:
        filters['min_amount'] = min_amount
    if max_amount is not None:
        filters['max_amount'] = max_amount
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if overdue_only:
        filters['overdue_only'] = overdue_only
    if search:
        filters['search'] = search
    expenses, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        sort_field=sort_by,
        sort_order=sort_order,
        filters=filters
    )
    expense_responses = [ExpenseListResponse.model_validate(expense) for expense in expenses]
    return create_legacy_expense_response(expense_responses, total, skip, limit)


@router.get("/overdue", response_model=OverdueExpensesListResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_overdue_expenses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all overdue invoice expenses."""
    service = ExpenseService(db)
    return await service.get_overdue_invoices(current_user.id)


@router.get("/stats", response_model=ExpenseStats)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_expense_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive expense statistics."""
    service = ExpenseService(db)
    return await service.get_expense_stats(current_user.id)


@router.get("/{expense_id}", response_model=ExpenseResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def get_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expense by ID with full relationships."""
    service = ExpenseService(db)
    expense = await service.get_by_id_or_raise(expense_id, current_user.id)
    return ExpenseResponse.model_validate(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def update_expense(
    expense_id: UUID,
    expense_data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update expense with tax recalculation if needed."""
    service = ExpenseService(db)
    expense = await service.update(expense_id, expense_data.model_dump(exclude_unset=True), current_user.id)
    return ExpenseResponse.model_validate(expense)


@router.delete("/{expense_id}", status_code=204)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def delete_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete expense with business rule validation."""
    service = ExpenseService(db)
    await service.delete(expense_id, current_user.id, soft=True)


@router.put("/{expense_id}/mark-paid", response_model=ExpenseResponse)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def mark_expense_paid(
    expense_id: UUID,
    payment_date: Optional[datetime] = Query(None, description="Payment date (defaults to current time)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark expense as paid and set payment date."""
    service = ExpenseService(db)
    expense = await service.mark_as_paid(expense_id, current_user.id, payment_date)
    return ExpenseResponse.model_validate(expense)


# Document Analysis & OCR (Google Vision API Integration)
# @router.post("/analyze-document", response_model=DocumentAnalysisResponse, status_code=201)
# @api_endpoint(handle_exceptions=True, log_calls=True)
# async def analyze_document(
#     file: UploadFile = File(..., description="Document to analyze (images or PDF)"),
#     analysis_type: str = Form(default="receipt", description="Type of document analysis"),
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Analyze document with Google Vision API and create analysis record."""
#     # Validate file type at route level for better error messages
#     if not file.content_type.startswith(('image/', 'application/pdf')):
#         from fastapi import HTTPException
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid file type. Only images and PDFs are supported."
#         )
    
#     # Create document analysis record
#     service = ExpenseService(db)
#     analysis = await service.create_document_analysis(
#         current_user.id,
#         DocumentAnalysisCreate(
#             original_filename=file.filename,
#             file_type=file.content_type,
#             analysis_status=AnalysisStatus.PENDING,
#             file_size=file.size if hasattr(file, 'size') else None
#         )
#     )
    
#     # TODO: Process file asynchronously with Google Vision API
#     # For now, return the pending analysis
    
#     return DocumentAnalysisResponse.model_validate(analysis)


# @router.get("/document-analysis/{analysis_id}", response_model=DocumentAnalysisResponse)
# @api_endpoint(handle_exceptions=True, log_calls=True)
# async def get_document_analysis(
#     analysis_id: UUID,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get document analysis results."""
#     service = ExpenseService(db)
#     # Get analysis using service method for proper validation
#     analysis = await service.get_document_analysis_by_id(analysis_id, current_user.id)
#     return DocumentAnalysisResponse.model_validate(analysis)


# @router.post("/create-from-analysis", response_model=ExpenseResponse, status_code=201)
# @api_endpoint(handle_exceptions=True, log_calls=True)
# async def create_expense_from_analysis(
#     analysis_id: UUID,
#     user_corrections: Optional[Dict[str, Any]] = None,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Create expense from document analysis results with user corrections."""
#     service = ExpenseService(db)
#     expense = await service.create_expense_from_analysis(
#         current_user.id,
#         analysis_id,
#         user_corrections
#     )
#     return ExpenseResponse.model_validate(expense)


# # File Management
# @router.post("/{expense_id}/attachments", response_model=AttachmentResponse, status_code=201)
# @api_endpoint(handle_exceptions=True, log_calls=True)
# async def upload_attachment(
#     expense_id: UUID,
#     file: UploadFile = File(..., description="File to attach to expense"),
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Upload attachment to expense with validation."""
#     # Basic file size validation at route level
#     MAX_FILE_SIZE = 52428800  # 50MB in bytes
#     if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
#         from fastapi import HTTPException
#         raise HTTPException(
#             status_code=400,
#             detail=f"File size too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB."
#         )
    
#     service = ExpenseService(db)
    
#     # TODO: Upload file to cloud storage and get URL
#     # For now, use a placeholder URL
#     file_url = f"https://storage.smartbudget360.com/{expense_id}/{file.filename}"
    
#     attachment_data = AttachmentCreate(
#         file_name=file.filename,
#         file_url=file_url,
#         file_type=file.content_type,
#         file_size=file.size if hasattr(file, 'size') else None
#     )
    
#     attachment = await service.add_attachment(current_user.id, expense_id, attachment_data)
#     return AttachmentResponse.model_validate(attachment)


# @router.get("/{expense_id}/attachments", response_model=List[AttachmentResponse])
# @api_endpoint(handle_exceptions=True, log_calls=True)
# async def get_expense_attachments(
#     expense_id: UUID,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get expense attachments."""
#     service = ExpenseService(db)
#     expense = await service.get_by_id_or_raise(expense_id, current_user.id)
    
#     # Return attachments (empty list if none)
#     return [AttachmentResponse.model_validate(a) for a in expense.attachments]


# Specialized Endpoints
@router.get("/types/{expense_type}", response_model=ExpenseListPaginatedResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_expenses_by_type(
    expense_type: ExpenseType,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expenses by type (simple or invoice)."""
    service = ExpenseService(db)
    expenses, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        sort_field="expense_date",
        sort_order="desc",
        filters={"expense_type": expense_type}
    )
    
    expense_list = [ExpenseListResponse.model_validate(expense) for expense in expenses]
    pages = (total + limit - 1) // limit if total > 0 and limit > 0 else 0
    
    return create_legacy_expense_response(expense_list, total, skip, limit)


@router.get("/invoices/list", response_model=ExpenseListPaginatedResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_invoice_expenses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    supplier_name: Optional[str] = Query(None, description="Filter by supplier name"),
    overdue_only: bool = Query(False, description="Show only overdue invoices"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get invoice expenses with filtering."""
    service = ExpenseService(db)
    
    # Build filter object for invoices only
    filters = {}
    if payment_status:
        filters['payment_status'] = payment_status
    if supplier_name:
        filters['supplier_name'] = supplier_name
    if overdue_only:
        filters['overdue_only'] = overdue_only
    
    expenses, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        sort_field="expense_date",
        sort_order="desc",
        filters=filters
    )
    
    expense_list = [ExpenseListResponse.model_validate(expense) for expense in expenses]
    pages = (total + limit - 1) // limit if total > 0 and limit > 0 else 0
    
    return create_legacy_expense_response(expense_list, total, skip, limit)


@router.get("/by-category/{category_id}", response_model=ExpenseListPaginatedResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_expenses_by_category(
    category_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    date_from: Optional[datetime] = Query(None, description="Filter expenses from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter expenses up to this date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expenses grouped by category."""
    service = ExpenseService(db)
    
    filters = {}
    if category_id:
        filters['category_id'] = category_id
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    
    expenses, total = await service.get_paginated(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        sort_field="expense_date",
        sort_order="desc",
        filters=filters
    )
    
    expense_list = [ExpenseListResponse.model_validate(expense) for expense in expenses]
    pages = (total + limit - 1) // limit if total > 0 and limit > 0 else 0
    
    return create_legacy_expense_response(expense_list, total, skip, limit)


# Additional convenience endpoints
@router.get("/recent/list", response_model=ExpenseListPaginatedResponse)
@api_endpoint(handle_exceptions=True, validate_pagination_params=True, log_calls=True)
async def get_recent_expenses(
    limit: int = Query(10, ge=1, le=50, description="Number of recent expenses to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent expenses for dashboard."""
    service = ExpenseService(db)
    expenses, total = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=limit,
        sort_field="expense_date",
        sort_order="desc"
    )
    
    expense_list = [ExpenseListResponse.model_validate(expense) for expense in expenses]
    
    return create_legacy_expense_response(expense_list, total, 0, limit)


@router.get("/search/quick")
@api_endpoint(handle_exceptions=True, log_calls=True)
async def quick_expense_search(
    q: str = Query(..., min_length=2, description="Search term (minimum 2 characters)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Quick search expenses for autocomplete."""
    service = ExpenseService(db)
    
    filters = ExpenseFilter(search=q)
    expenses, total = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=limit,
        sort_field="expense_date",
        sort_order="desc",
        filters=filters.model_dump()
    )
    
    # Return simplified format for autocomplete
    return [
        {
            "id": str(expense.id),
            "description": expense.description,
            "total_amount": float(expense.total_amount),
            "expense_date": expense.expense_date,
            "expense_type": expense.expense_type.value
        }
        for expense in expenses
    ]


@router.post("/{expense_id}/archive", status_code=204)
@api_endpoint(handle_exceptions=True, log_calls=True)
async def archive_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive an expense (alias for delete)."""
    service = ExpenseService(db)
    await service.delete(expense_id, current_user.id, soft=True)


@router.get("/export/summary")
@api_endpoint(handle_exceptions=True, log_calls=True)
async def export_expenses_summary(
    date_from: Optional[datetime] = Query(None, description="Export from this date"),
    date_to: Optional[datetime] = Query(None, description="Export up to this date"),
    expense_type: Optional[ExpenseType] = Query(None, description="Filter by expense type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export expenses summary for reporting."""
    service = ExpenseService(db)
    
    filters = ExpenseFilter(
        expense_type=expense_type,
        date_from=date_from,
        date_to=date_to
    )
    
    expenses, total = await service.get_paginated(
        user_id=current_user.id,
        skip=0,
        limit=10000,  # High limit for export
        sort_field="expense_date",
        sort_order="desc",
        filters=filters.model_dump()
    )
    
    # Return summary data - could generate CSV/PDF in real implementation
    return {
        "message": "Export functionality - implement file generation",
        "total_expenses": total,
        "total_amount": sum(float(exp.total_amount) for exp in expenses),
        "expense_type": expense_type.value if expense_type else "ALL",
        "date_range": {
            "from": date_from,
            "to": date_to
        }
    }