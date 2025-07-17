import { 
  Expense, 
  ExpenseFilters, 
  PaginatedExpenseResponse, 
  ExpenseStats,
  CreateExpensePayload,
  UpdateExpensePayload,
  ExpenseType
} from "@/lib/types/expenses"
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
    console.log('Creating expense with data:', data)
    const endpoint = data.expense_type === ExpenseType.invoice ? 'invoice' : 'simple'
    const response = await fetch(`${API_BASE}/expenses/${endpoint}`, {
    method: "POST",
    headers: await getAuthHeaders(),
      body: JSON.stringify({
        description: data.description,
        expense_date: data.expense_date,
        notes: data.notes,
        receipt_url: data.receipt_url,
        category_id: data.category_id,
        payment_method: data.payment_method,
        total_amount: data.total_amount,
        currency: data.currency || 'EUR',
        tags: data.tags || [],
        custom_fields: data.custom_fields || {},
        // Only include invoice-specific fields for invoice type
        ...(data.expense_type === ExpenseType.invoice && {
          supplier_name: data.custom_fields?.supplier_name,
          supplier_tax_id: data.custom_fields?.supplier_tax_id,
          invoice_number: data.custom_fields?.invoice_number,
          payment_due_date: data.custom_fields?.due_date
        })
  })
    })

    const responseData = await response.json()
    console.log('Response:', { status: response.status, data: responseData })

  if (!response.ok) {
      if (typeof responseData === 'object' && responseData.detail) {
        throw new Error(responseData.detail)
      } else {
        console.error('Unexpected error format:', responseData)
        throw new Error(JSON.stringify(responseData))
      }
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
