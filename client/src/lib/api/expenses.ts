import { apiClient } from './client'
import { 
  CreateExpensePayload, 
  UpdateExpensePayload, 
  Expense,
  PaginatedExpenseResponse,
  ExpenseFilters,
  ExpenseStats,
  BulkDeleteRequest,
  BulkDeleteResponse,
  BulkUpdateRequest,
  BulkUpdateResponse
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
   * Create new expense
   */
  async createExpense(expenseData: CreateExpensePayload): Promise<Expense> {
    // Determine endpoint based on expense type
    const endpoint = expenseData.expense_type === 'INVOICE' 
      ? '/expenses/invoice' 
      : '/expenses/simple'
    
    const response = await apiClient.post<Expense>(endpoint, expenseData)
    return response.data
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
}

// Export singleton instance
export const expensesApi = new ExpensesApiClient()