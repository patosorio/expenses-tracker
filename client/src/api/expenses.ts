import { 
  Expense, 
  ExpenseFilters, 
  PaginatedExpenseResponse, 
  ExpenseStats,
  CreateExpensePayload,
  UpdateExpensePayload,
  ExpenseType
} from "@/types/expenses"
import { UUID } from "crypto"
import { apiClient } from "./client"

export class ExpensesApi {
  /**
   * Get paginated list of expenses with filters
   */
  async getExpenses(
    page: number = 1,
    limit: number = 10,
    filters?: ExpenseFilters,
    sortBy: string = "expense_date",
    sortOrder: "asc" | "desc" = "desc"
  ): Promise<PaginatedExpenseResponse> {
    const skip = (page - 1) * limit
    const searchParams = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(filters?.expense_type && { expense_type: filters.expense_type }),
      ...(filters?.payment_status && { payment_status: filters.payment_status }),
      ...(filters?.payment_method && { payment_method: filters.payment_method }),
      ...(filters?.category_id && { category_id: filters.category_id.toString() }),
      ...(filters?.supplier_name && { supplier_name: filters.supplier_name }),
      ...(filters?.min_amount && { min_amount: filters.min_amount.toString() }),
      ...(filters?.max_amount && { max_amount: filters.max_amount.toString() }),
      ...(filters?.date_from && { date_from: filters.date_from }),
      ...(filters?.date_to && { date_to: filters.date_to }),
      ...(filters?.overdue_only && { overdue_only: filters.overdue_only.toString() }),
      ...(filters?.search && { search: filters.search })
    })

    const response = await apiClient.get<PaginatedExpenseResponse>(`/expenses/?${searchParams}`)
    return response.data
  }

  /**
   * Get a single expense by ID
   */
  async getExpenseById(id: UUID): Promise<Expense> {
    const response = await apiClient.get<Expense>(`/expenses/${id}`)
    return response.data
  }

  /**
   * Create a new expense
   */
  async createExpense(data: CreateExpensePayload): Promise<Expense> {
    const endpoint = data.expense_type === ExpenseType.INVOICE ? 'invoice' : 'simple'
    
    // Prepare the request body based on expense type
    const requestBody: Record<string, unknown> = {
      description: data.description,
      expense_date: data.expense_date + 'T00:00:00', // Convert to ISO datetime format
      notes: data.notes,
      receipt_url: data.receipt_url,
      category_id: data.category_id,
      total_amount: data.total_amount,
      currency: data.currency || 'EUR',
      tags: data.tags || [],
    }

    if (data.expense_type === ExpenseType.SIMPLE) {
      // For simple expenses
      requestBody.payment_method = data.payment_method
      if (data.custom_fields?.contact_id) {
        requestBody.contact_id = data.custom_fields.contact_id
      }
    } else {
      // For invoice expenses
      requestBody.contact_id = data.custom_fields?.contact_id
      requestBody.base_amount = data.custom_fields?.base_amount || data.total_amount
      requestBody.tax_amount = data.custom_fields?.tax_amount || 0
      requestBody.invoice_number = data.custom_fields?.invoice_number
      requestBody.payment_due_date = data.custom_fields?.payment_due_date ? 
        data.custom_fields.payment_due_date + 'T00:00:00' : undefined
      if (data.payment_method) {
        requestBody.payment_method = data.payment_method
      }
    }

    const response = await apiClient.post<Expense>(`/expenses/${endpoint}`, requestBody)
    return response.data
  }

  /**
   * Update an existing expense
   */
  async updateExpense(id: UUID, data: UpdateExpensePayload): Promise<Expense> {
    const response = await apiClient.put<Expense>(`/expenses/${id}`, data)
    return response.data
  }

  /**
   * Delete an expense
   */
  async deleteExpense(id: UUID): Promise<void> {
    await apiClient.delete<void>(`/expenses/${id}`)
  }

  /**
   * Mark an expense as paid
   */
  async markExpensePaid(id: UUID, paymentDate?: string): Promise<Expense> {
    const response = await apiClient.put<Expense>(`/expenses/${id}/mark-paid`, { payment_date: paymentDate })
    return response.data
  }

  /**
   * Get expense statistics
   */
  async getExpenseStats(): Promise<ExpenseStats> {
    const response = await apiClient.get<ExpenseStats>('/expenses/stats')
    return response.data
  }
}

// Export a singleton instance
export const expensesApi = new ExpensesApi();
