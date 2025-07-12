from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from src.expenses.service import ExpenseService
from src.expenses.schemas import (
    # Request schemas
    SimpleExpenseCreate, InvoiceExpenseCreate, ExpenseUpdate,
    TaxConfigCreate, TaxConfigUpdate, AttachmentCreate, DocumentAnalysisCreate,
    ExpenseFilter,
    
    # Response schemas
    ExpenseResponse, ExpenseListResponse, ExpenseListPaginatedResponse,
    TaxConfigResponse, AttachmentResponse, DocumentAnalysisResponse,
    ExpensePreviewResponse, OverdueExpensesListResponse, ExpenseStats,
    ExpenseSummary
)
from src.expenses.models import ExpenseType, PaymentMethod, PaymentStatus, AnalysisStatus
from src.auth.dependencies import get_current_user
from src.users.models import User
from src.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


# Core CRUD Operations
@router.post("/simple", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_simple_expense(
    expense_data: SimpleExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a simple (receipt) expense"""
    try:
        service = ExpenseService(db)
        expense = await service.create_simple_expense(current_user.id, expense_data)
        return expense
    except Exception as e:
        logger.error(f"Error creating simple expense: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create expense: {str(e)}"
        )


@router.post("/invoice", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_expense(
    expense_data: InvoiceExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an invoice expense with tax calculations"""
    try:
        service = ExpenseService(db)
        expense = await service.create_invoice_expense(current_user.id, expense_data)
        return expense
    except Exception as e:
        logger.error(f"Error creating invoice expense: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create invoice expense: {str(e)}"
        )


@router.get("/", response_model=ExpenseListPaginatedResponse)
async def get_expenses(
    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    
    # Filtering
    expense_type: Optional[ExpenseType] = None,
    payment_status: Optional[PaymentStatus] = None,
    payment_method: Optional[PaymentMethod] = None,
    category_id: Optional[UUID] = None,
    supplier_name: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    overdue_only: bool = False,
    search: Optional[str] = None,
    
    # Sorting
    sort_by: str = Query("expense_date", pattern="^(expense_date|total_amount|description|supplier_name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expenses with advanced filtering and pagination"""
    try:
        service = ExpenseService(db)
        
        # Build filter object
        filters = ExpenseFilter(
            expense_type=expense_type,
            payment_status=payment_status,
            payment_method=payment_method,
            category_id=category_id,
            supplier_name=supplier_name,
            min_amount=min_amount,
            max_amount=max_amount,
            date_from=date_from,
            date_to=date_to,
            overdue_only=overdue_only,
            search=search
        )
        
        expenses, total = await service.get_expenses_with_filters(
            current_user.id, filters, skip, limit, sort_by, sort_order
        )
        
        # Convert to list response format
        expense_list = [ExpenseListResponse.model_validate(expense) for expense in expenses]
        
        pages = (total + limit - 1) // limit
        
        return ExpenseListPaginatedResponse(
            expenses=expense_list,
            total=total,
            page=(skip // limit) + 1,
            per_page=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting expenses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve expenses"
        )


@router.get("/overdue", response_model=OverdueExpensesListResponse)
async def get_overdue_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all overdue invoice expenses"""
    try:
        service = ExpenseService(db)
        return await service.get_overdue_expenses(current_user.id)
    except Exception as e:
        logger.error(f"Error getting overdue expenses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overdue expenses"
        )


@router.get("/stats", response_model=ExpenseStats)
async def get_expense_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive expense statistics"""
    try:
        service = ExpenseService(db)
        return await service.get_expense_stats(current_user.id)
    except Exception as e:
        logger.error(f"Error getting expense stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve expense statistics"
        )


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense by ID with full relationships"""
    try:
        service = ExpenseService(db)
        expense = await service.get_expense_by_id(current_user.id, expense_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        return expense
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting expense {expense_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve expense"
        )


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: UUID,
    expense_data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update expense with tax recalculation if needed"""
    try:
        service = ExpenseService(db)
        expense = await service.update_expense(current_user.id, expense_id, expense_data)
        return expense
    except Exception as e:
        logger.error(f"Error updating expense {expense_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update expense: {str(e)}"
        )


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete expense"""
    try:
        service = ExpenseService(db)
        await service.delete_expense(current_user.id, expense_id)
    except Exception as e:
        logger.error(f"Error deleting expense {expense_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete expense: {str(e)}"
        )


@router.put("/{expense_id}/mark-paid", response_model=ExpenseResponse)
async def mark_expense_paid(
    expense_id: UUID,
    payment_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark expense as paid and set payment date"""
    try:
        service = ExpenseService(db)
        expense = await service.mark_expense_as_paid(current_user.id, expense_id, payment_date)
        return expense
    except Exception as e:
        logger.error(f"Error marking expense {expense_id} as paid: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to mark expense as paid: {str(e)}"
        )


# Tax Configuration Management
@router.get("/tax-configs", response_model=List[TaxConfigResponse])
async def get_tax_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's tax configurations"""
    try:
        service = ExpenseService(db)
        tax_configs = await service.get_user_tax_configs(current_user.id)
        return tax_configs
    except Exception as e:
        logger.error(f"Error getting tax configs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tax configurations"
        )


@router.post("/tax-configs", response_model=TaxConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_config(
    tax_data: TaxConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create tax configuration"""
    try:
        service = ExpenseService(db)
        tax_config = await service.create_tax_config(current_user.id, tax_data)
        return tax_config
    except Exception as e:
        logger.error(f"Error creating tax config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tax configuration: {str(e)}"
        )


# Document Analysis & OCR (Google Vision API Integration)
@router.post("/analyze-document", response_model=DocumentAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_document(
    file: UploadFile = File(...),
    analysis_type: str = Form(default="receipt"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and analyze document with Google Vision API"""
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Please upload PDF, JPEG, PNG, or TIFF files."
            )
        
        # Validate file size (50MB max)
        if file.size > 52428800:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum size is 50MB."
            )
        
        service = ExpenseService(db)
        
        # Create document analysis record
        analysis_data = DocumentAnalysisCreate(
            original_filename=file.filename,
            file_type=file.content_type,
            analysis_status=AnalysisStatus.PENDING
        )
        
        analysis = await service.create_document_analysis(current_user.id, analysis_data)
        
        # TODO: Integrate with Google Vision API here
        # This would involve:
        # 1. Upload file to cloud storage
        # 2. Process with Google Vision API
        # 3. Extract structured data
        # 4. Update analysis record with results
        
        # For now, return the analysis record
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze document"
        )


@router.get("/document-analysis/{analysis_id}", response_model=DocumentAnalysisResponse)
async def get_document_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document analysis results"""
    try:
        service = ExpenseService(db)
        # Get analysis (implementation would need to be added to service)
        analysis = db.query(DocumentAnalysis).filter(
            and_(DocumentAnalysis.id == analysis_id, DocumentAnalysis.user_id == current_user.id)
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document analysis not found"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document analysis"
        )


@router.post("/create-from-analysis", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense_from_analysis(
    analysis_id: UUID,
    user_corrections: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create expense from OCR analysis results"""
    try:
        service = ExpenseService(db)
        expense = await service.create_expense_from_analysis(
            current_user.id, analysis_id, user_corrections
        )
        return expense
    except Exception as e:
        logger.error(f"Error creating expense from analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create expense from analysis: {str(e)}"
        )


# File Management
@router.post("/{expense_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    expense_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload attachment to expense"""
    try:
        # Validate file size
        if file.size > 52428800:  # 50MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum size is 50MB."
            )
        
        service = ExpenseService(db)
        
        # TODO: Upload file to cloud storage and get URL
        file_url = f"https://storage.example.com/{expense_id}/{file.filename}"
        
        attachment_data = AttachmentCreate(
            file_name=file.filename,
            file_url=file_url,
            file_type=file.content_type,
            file_size=file.size
        )
        
        attachment = await service.add_attachment(current_user.id, expense_id, attachment_data)
        return attachment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading attachment to expense {expense_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload attachment"
        )


@router.get("/{expense_id}/attachments", response_model=List[AttachmentResponse])
async def get_expense_attachments(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense attachments"""
    try:
        service = ExpenseService(db)
        expense = await service.get_expense_by_id(current_user.id, expense_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        return expense.attachments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attachments for expense {expense_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attachments"
        )


# Specialized Endpoints
@router.get("/invoices", response_model=ExpenseListPaginatedResponse)
async def get_invoice_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    payment_status: Optional[PaymentStatus] = None,
    supplier_name: Optional[str] = None,
    overdue_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get only invoice expenses with specialized filtering"""
    try:
        service = ExpenseService(db)
        
        filters = ExpenseFilter(
            expense_type=ExpenseType.INVOICE,
            payment_status=payment_status,
            supplier_name=supplier_name,
            overdue_only=overdue_only
        )
        
        expenses, total = await service.get_expenses_with_filters(
            current_user.id, filters, skip, limit
        )
        
        expense_list = [ExpenseListResponse.model_validate(expense) for expense in expenses]
        pages = (total + limit - 1) // limit
        
        return ExpenseListPaginatedResponse(
            expenses=expense_list,
            total=total,
            page=(skip // limit) + 1,
            per_page=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting invoice expenses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice expenses"
        )


@router.get("/by-category/{category_id}", response_model=ExpenseListPaginatedResponse)
async def get_expenses_by_category(
    category_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expenses grouped by category"""
    try:
        service = ExpenseService(db)
        
        filters = ExpenseFilter(
            category_id=category_id,
            date_from=date_from,
            date_to=date_to
        )
        
        expenses, total = await service.get_expenses_with_filters(
            current_user.id, filters, skip, limit
        )
        
        expense_list = [ExpenseListResponse.model_validate(expense) for expense in expenses]
        pages = (total + limit - 1) // limit
        
        return ExpenseListPaginatedResponse(
            expenses=expense_list,
            total=total,
            page=(skip // limit) + 1,
            per_page=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting expenses by category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve expenses by category"
        )


# Import missing dependencies
from src.expenses.models import DocumentAnalysis
from sqlalchemy import and_
