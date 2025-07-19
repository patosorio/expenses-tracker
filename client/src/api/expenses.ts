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
import { getAuth } from "firebase/auth"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const API_BASE = `${API_URL}/api/v1`

async function getAuthHeaders() {
  const auth = getAuth()
  const token = await auth.currentUser?.getIdToken()
  return {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  }
}

export async function getExpenses(
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

  const response = await fetch(`${API_BASE}/expenses/?${searchParams}`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch expenses")
  }

  return response.json()
}

export async function getExpenseById(id: UUID): Promise<Expense> {
  const response = await fetch(`${API_BASE}/expenses/${id}`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch expense")
  }

  return response.json()
}

export async function createExpense(data: CreateExpensePayload): Promise<Expense> {
  try {
    const endpoint = data.expense_type === ExpenseType.INVOICE ? 'invoice' : 'simple'
    
    // Prepare the request body based on expense type
    const requestBody: any = {
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

    const response = await fetch(`${API_BASE}/expenses/${endpoint}`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(requestBody)
    })

    const responseData = await response.json()

    if (!response.ok) {
      console.error('Backend error response:', responseData)
      
      let errorMessage = "Failed to create expense"
      if (typeof responseData === 'object') {
        if (responseData.detail) {
          // Handle array of validation errors
          if (Array.isArray(responseData.detail)) {
            errorMessage = responseData.detail.map((error: any) => 
              error.msg || error.message || JSON.stringify(error)
            ).join(', ')
          } else {
            errorMessage = responseData.detail
          }
        } else if (responseData.message) {
          errorMessage = responseData.message
        } else {
          errorMessage = JSON.stringify(responseData)
        }
      } else if (typeof responseData === 'string') {
        errorMessage = responseData
      }
      
      throw new Error(errorMessage)
    }

    return responseData
  } catch (error) {
    console.error('Error in createExpense:', error)
    if (error instanceof Error) {
      throw error
    } else {
      throw new Error('An unexpected error occurred while creating the expense')
    }
  }
}

export async function updateExpense(id: UUID, data: UpdateExpensePayload): Promise<Expense> {
  const response = await fetch(`${API_BASE}/expenses/${id}`, {
    method: "PUT",
    headers: await getAuthHeaders(),
    body: JSON.stringify(data)
  })

  if (!response.ok) {
    throw new Error("Failed to update expense")
  }

  return response.json()
}

export async function deleteExpense(id: UUID): Promise<void> {
  const response = await fetch(`${API_BASE}/expenses/${id}`, {
    method: "DELETE",
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to delete expense")
  }
}

export async function markExpensePaid(id: UUID, paymentDate?: string): Promise<Expense> {
  const response = await fetch(`${API_BASE}/expenses/${id}/mark-paid`, {
    method: "PUT",
    headers: await getAuthHeaders(),
    body: JSON.stringify({ payment_date: paymentDate })
  })

  if (!response.ok) {
    throw new Error("Failed to mark expense as paid")
  }

  return response.json()
}

export async function getExpenseStats(): Promise<ExpenseStats> {
  const response = await fetch(`${API_BASE}/expenses/stats`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch expense stats")
  }

  return response.json()
}
