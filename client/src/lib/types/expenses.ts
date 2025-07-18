import { UUID } from "crypto"

export enum ExpenseType {
  simple = "simple",
  invoice = "invoice"
}

export enum PaymentMethod {
  CASH = "cash",
  CARD = "card",
  BANK_TRANSFER = "bank_transfer",
  DIGITAL_WALLET = "digital_wallet"
}

export enum PaymentStatus {
  PENDING = "pending",
  PAID = "paid",
  REFUNDED = "refunded"
}

export interface Expense {
  id: UUID
  description: string
  expense_date: string
  expense_type: ExpenseType
  notes?: string
  receipt_url?: string
  invoice_number?: string
  payment_due_date?: string
  base_amount: number
  tax_amount: number
  total_amount: number
  currency: string
  payment_status: PaymentStatus
  payment_method: PaymentMethod
  payment_date?: string
  category_id: UUID
  contact_id?: UUID
  tax_config_id?: UUID
  tags?: string[]
  custom_fields?: Record<string, any>
  is_overdue: boolean
  days_overdue: number
  created_at: string
  updated_at?: string
  is_active: boolean
}

export interface ExpenseFilters {
  expense_type?: ExpenseType
  payment_status?: PaymentStatus
  payment_method?: PaymentMethod
  category_id?: UUID
  supplier_name?: string
  min_amount?: number
  max_amount?: number
  date_from?: string
  date_to?: string
  overdue_only?: boolean
  search?: string
}

export interface PaginatedExpenseResponse {
  expenses: Expense[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface ExpenseStats {
  total_expenses: number
  total_count: number
  pending_payments: number
  overdue_count: number
  overdue_amount: number
  this_month_total: number
  last_month_total: number
  monthly_change_percent: number
  top_categories: Array<{
    category_id: UUID
    category_name: string
    total_amount: number
    percentage: number
  }>
  top_suppliers: Array<{
    supplier_name: string
    total_amount: number
    transaction_count: number
  }>
}

export interface CreateExpensePayload {
  description: string
  expense_date: string  // ISO date string
  category_id: UUID
  payment_method: PaymentMethod
  total_amount: number
  notes?: string
  receipt_url?: string
  currency?: string
  tags?: string[]
  custom_fields?: Record<string, any>
  expense_type?: ExpenseType
}

export interface UpdateExpensePayload {
  description?: string
  expense_date?: string
  notes?: string
  receipt_url?: string
  category_id?: UUID
  payment_method?: PaymentMethod
  payment_status?: PaymentStatus
  payment_date?: string
  total_amount?: number
  currency?: string
  tags?: string[]
  custom_fields?: Record<string, any>
}
