import { apiClient } from './client'
import { 
  CreateSimpleExpensePayload,
  CreateInvoiceExpensePayload,
  CreateExpensePayload,
  UpdateExpensePayload, 
  Expense,
  PaginatedExpenseResponse,
  ExpenseFilters,
  ExpenseStats,
  BulkDeleteRequest,
  BulkDeleteResponse,
  BulkUpdateRequest,
  BulkUpdateResponse,
  InvoiceFilters,
  OverdueExpensesListResponse,
  ExpenseAttachment,
  DocumentAnalysis,
  QuickSearchResult
} from '@/lib/types/expenses'

/**
 * Pure API layer for expenses - only HTTP requests, no business logic
 */
export class ExpensesApiClient {
  /**
   * Get paginated expenses with filters
   */
  async getExpenses(
    page: number = 1,
    limit: number = 25,
    filters: ExpenseFilters = {},
    sortBy: string = 'expense_date',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<PaginatedExpenseResponse> {
    const params = new URLSearchParams({
      skip: ((page - 1) * limit).toString(),
      limit: limit.toString(),
      sort_by: sortBy,
      sort_order: sortOrder
    })

    // Add filters to params
    if (filters.search) params.append('search', filters.search)
    if (filters.expense_type) params.append('expense_type', filters.expense_type)
    if (filters.payment_status) params.append('payment_status', filters.payment_status)
    if (filters.payment_method) params.append('payment_method', filters.payment_method)
    if (filters.category_id) params.append('category_id', filters.category_id)
    if (filters.supplier_name) params.append('supplier_name', filters.supplier_name)
    if (filters.min_amount !== undefined) params.append('min_amount', filters.min_amount.toString())
    if (filters.max_amount !== undefined) params.append('max_amount', filters.max_amount.toString())
    if (filters.date_from) params.append('date_from', filters.date_from)
    if (filters.date_to) params.append('date_to', filters.date_to)

    const response = await apiClient.get<PaginatedExpenseResponse>(`/expenses?${params}`)
    return response.data
  }

  /**
   * Get expense by ID
   */
  async getExpenseById(id: string): Promise<Expense> {
    const response = await apiClient.get<Expense>(`/expenses/${id}`)
    return response.data
  }

  /**
   * Create simple (receipt) expense
   */
  async createSimpleExpense(expenseData: CreateSimpleExpensePayload): Promise<Expense> {
    const response = await apiClient.post<Expense>('/expenses/simple', expenseData)
    return response.data
  }

  /**
   * Create invoice expense
   */
  async createInvoiceExpense(expenseData: CreateInvoiceExpensePayload): Promise<Expense> {
    const response = await apiClient.post<Expense>('/expenses/invoice', expenseData)
    return response.data
  }

  /**
   * Create expense (legacy method for backward compatibility)
   * Determines the correct endpoint based on expense type
   */
  async createExpense(expenseData: CreateExpensePayload): Promise<Expense> {
    if (expenseData.expense_type === 'INVOICE') {
      return this.createInvoiceExpense(expenseData as CreateInvoiceExpensePayload)
    } else {
      return this.createSimpleExpense(expenseData as CreateSimpleExpensePayload)
    }
  }

  /**
   * Update expense
   */
  async updateExpense(id: string, updateData: UpdateExpensePayload): Promise<Expense> {
    const response = await apiClient.put<Expense>(`/expenses/${id}`, updateData)
    return response.data
  }

  /**
   * Delete expense
   */
  async deleteExpense(id: string): Promise<void> {
    await apiClient.delete(`/expenses/${id}`)
  }

  /**
   * Mark expense as paid
   */
  async markExpenseAsPaid(id: string, paymentDate?: string): Promise<Expense> {
    const params = paymentDate ? `?payment_date=${paymentDate}` : ''
    const response = await apiClient.put<Expense>(`/expenses/${id}/mark-paid${params}`)
    return response.data
  }

  /**
   * Get expense statistics
   */
  async getExpenseStats(): Promise<ExpenseStats> {
    const response = await apiClient.get<ExpenseStats>('/expenses/stats')
    return response.data
  }

  /**
   * Bulk delete expenses
   */
  async bulkDeleteExpenses(request: BulkDeleteRequest): Promise<BulkDeleteResponse> {
    const response = await apiClient.post<BulkDeleteResponse>('/expenses/bulk-delete', request)
    return response.data
  }

  /**
   * Bulk update expenses
   */
  async bulkUpdateExpenses(request: BulkUpdateRequest): Promise<BulkUpdateResponse> {
    const response = await apiClient.post<BulkUpdateResponse>('/expenses/bulk-update', request)
    return response.data
  }

  /**
   * Upload receipt/document for OCR processing
   */
  async uploadReceiptForOCR(file: File, expenseId?: string): Promise<{ analysisId: string }> {
    const formData = new FormData()
    formData.append('file', file)
    if (expenseId) formData.append('expense_id', expenseId)

    const response = await apiClient.post<{ analysisId: string }>('/expenses/analyze-document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }

  /**
   * Get OCR analysis results
   */
  async getOCRAnalysis(analysisId: string): Promise<any> {
    const response = await apiClient.get(`/expenses/document-analysis/${analysisId}`)
    return response.data
  }

  /**
   * Create expense from OCR analysis
   */
  async createExpenseFromOCR(
    analysisId: string, 
    userCorrections?: Record<string, any>
  ): Promise<Expense> {
    const response = await apiClient.post<Expense>('/expenses/create-from-analysis', {
      analysis_id: analysisId,
      user_corrections: userCorrections
    })
    return response.data
  }

  /**
   * Search vendors and suppliers for contacts
   */
  async searchVendorsAndSuppliers(query: string, limit: number = 10): Promise<any[]> {
    const params = new URLSearchParams({
      search: query,
      limit: limit.toString(),
      contact_type: 'VENDOR,SUPPLIER'
    })
    
    const response = await apiClient.get<any[]>(`/contacts/search?${params}`)
    return response.data
  }

  // ===== SPECIALIZED API METHODS =====

  /**
   * Get expenses by type (simple or invoice)
   */
  async getExpensesByType(
    expenseType: 'SIMPLE' | 'INVOICE',
    page: number = 1,
    limit: number = 25
  ): Promise<PaginatedExpenseResponse> {
    const params = new URLSearchParams({
      skip: ((page - 1) * limit).toString(),
      limit: limit.toString()
    })

    const response = await apiClient.get<PaginatedExpenseResponse>(`/expenses/types/${expenseType}?${params}`)
    return response.data
  }

  /**
   * Get invoice expenses with filtering
   */
  async getInvoiceExpenses(
    page: number = 1,
    limit: number = 25,
    filters: InvoiceFilters = {}
  ): Promise<PaginatedExpenseResponse> {
    const params = new URLSearchParams({
      skip: ((page - 1) * limit).toString(),
      limit: limit.toString()
    })

    // Add filters
    if (filters.payment_status) params.append('payment_status', filters.payment_status)
    if (filters.supplier_name) params.append('supplier_name', filters.supplier_name)
    if (filters.overdue_only) params.append('overdue_only', 'true')

    const response = await apiClient.get<PaginatedExpenseResponse>(`/expenses/invoices/list?${params}`)
    return response.data
  }

  /**
   * Get expenses by category
   */
  async getExpensesByCategory(
    categoryId: string,
    page: number = 1,
    limit: number = 25,
    dateFrom?: string,
    dateTo?: string
  ): Promise<PaginatedExpenseResponse> {
    const params = new URLSearchParams({
      skip: ((page - 1) * limit).toString(),
      limit: limit.toString()
    })

    if (dateFrom) params.append('date_from', dateFrom)
    if (dateTo) params.append('date_to', dateTo)

    const response = await apiClient.get<PaginatedExpenseResponse>(`/expenses/by-category/${categoryId}?${params}`)
    return response.data
  }

  /**
   * Get recent expenses
   */
  async getRecentExpenses(limit: number = 10): Promise<PaginatedExpenseResponse> {
    const params = new URLSearchParams({
      limit: limit.toString()
    })

    const response = await apiClient.get<PaginatedExpenseResponse>(`/expenses/recent/list?${params}`)
    return response.data
  }

  /**
   * Quick expense search
   */
  async quickExpenseSearch(query: string, limit: number = 10): Promise<QuickSearchResult[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString()
    })

    const response = await apiClient.get<QuickSearchResult[]>(`/expenses/search/quick?${params}`)
    return response.data
  }

  /**
   * Get overdue expenses
   */
  async getOverdueExpenses(): Promise<OverdueExpensesListResponse> {
    const response = await apiClient.get<OverdueExpensesListResponse>('/expenses/overdue')
    return response.data
  }

  /**
   * Export expenses summary
   */
  async exportExpensesSummary(filters: {
    dateFrom?: string
    dateTo?: string
    expenseType?: string
  } = {}): Promise<any> {
    const params = new URLSearchParams()

    if (filters.dateFrom) params.append('date_from', filters.dateFrom)
    if (filters.dateTo) params.append('date_to', filters.dateTo)
    if (filters.expenseType) params.append('expense_type', filters.expenseType)

    const response = await apiClient.get(`/expenses/export/summary?${params}`)
    return response.data
  }

  /**
   * Get expense attachments
   */
  async getExpenseAttachments(expenseId: string): Promise<ExpenseAttachment[]> {
    const response = await apiClient.get<ExpenseAttachment[]>(`/expenses/${expenseId}/attachments`)
    return response.data
  }

  /**
   * Upload expense attachment
   */
  async uploadAttachment(expenseId: string, file: File): Promise<ExpenseAttachment> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<ExpenseAttachment>(`/expenses/${expenseId}/attachments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }

  /**
   * Get document analysis
   */
  async getDocumentAnalysis(analysisId: string): Promise<DocumentAnalysis> {
    const response = await apiClient.get<DocumentAnalysis>(`/expenses/document-analysis/${analysisId}`)
    return response.data
  }

  /**
   * Create expense from document analysis
   */
  async createExpenseFromAnalysis(
    analysisId: string,
    userCorrections?: Record<string, any>
  ): Promise<Expense> {
    const response = await apiClient.post<Expense>('/expenses/create-from-analysis', {
      analysis_id: analysisId,
      user_corrections: userCorrections
    })
    return response.data
  }
}

// Export singleton instance
export const expensesApi = new ExpensesApiClient()