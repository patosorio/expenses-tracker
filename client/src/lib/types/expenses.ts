import { UUID } from "crypto"

export enum ExpenseType {
  SIMPLE = "SIMPLE",
  INVOICE = "INVOICE"
}

export enum PaymentMethod {
  CASH = "CASH",
  CARD = "CARD",
  BANK_TRANSFER = "BANK_TRANSFER",
  DIGITAL_WALLET = "DIGITAL_WALLET"
}

export enum PaymentStatus {
  PENDING = "PENDING",
  PAID = "PAID",
  REFUNDED = "REFUNDED"
}

export interface Expense {
  id: string
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
  category_id: string
  contact_id?: string
  tax_config_id?: string
  tags?: string[]
  custom_fields?: Record<string, any>
  user_id: string
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

// Separate payload types for simple and invoice expenses
export interface CreateSimpleExpensePayload {
  description: string
  expense_date: string
  expense_type: ExpenseType.SIMPLE
  notes?: string
  receipt_url?: string
  category_id: UUID
  payment_method: PaymentMethod
  total_amount: number
  currency?: string
  tags?: string[]
  custom_fields?: Record<string, any>
}

export interface CreateInvoiceExpensePayload {
  description: string
  expense_date: string
  expense_type: ExpenseType.INVOICE
  notes?: string
  receipt_url?: string
  category_id: UUID
  payment_method?: PaymentMethod
  payment_due_date?: string
  invoice_number?: string
  contact_id: UUID
  base_amount: number
  tax_config_id?: UUID
  currency?: string
  tags?: string[]
  custom_fields?: Record<string, any>
}

// Union type for backward compatibility
export type CreateExpensePayload = CreateSimpleExpensePayload | CreateInvoiceExpensePayload

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
  invoice_number?: string
  payment_due_date?: string
  base_amount?: number
  tax_amount?: number
}

export interface UseExpensesOptions {
  page?: number
  limit?: number
  filters?: ExpenseFilters
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  enabled?: boolean
}

export interface UseExpensesReturn {
  expenses: Expense[]
  total: number
  pages: number
  currentPage: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  setPage: (page: number) => void
  setFilters: (filters: ExpenseFilters) => void
  setSort: (sortBy: string, sortOrder: 'asc' | 'desc') => void
}

// Bulk operation types
export interface BulkDeleteRequest {
  expense_ids: string[]
  reason?: string
}

export interface BulkDeleteResponse {
  deleted_count: number
  failed_count: number
  errors?: Array<{
    expense_id: string
    error: string
  }>
}

export interface BulkUpdateRequest {
  expense_ids: string[]
  update_data: Partial<UpdateExpensePayload>
}

export interface BulkUpdateResponse {
  updated_count: number
  failed_count: number
  errors?: Array<{
    expense_id: string
    error: string
  }>
}

// ===== SPECIALIZED TYPES =====

export interface InvoiceFilters {
  payment_status?: PaymentStatus
  supplier_name?: string
  overdue_only?: boolean
}

export interface CategoryExpenseFilters {
  dateFrom?: string
  dateTo?: string
}

export interface ExportExpenseFilters {
  dateFrom?: string
  dateTo?: string
  expenseType?: ExpenseType
}

export interface OverdueExpenseResponse {
  id: string
  description: string
  contact_name: string
  invoice_number?: string
  total_amount: number
  payment_due_date: string
  days_overdue: number
  currency: string
}

export interface OverdueExpensesListResponse {
  overdue_invoices: OverdueExpenseResponse[]
  total_overdue_amount: number
  count: number
  currency: string
}

export interface ExpenseAttachment {
  id: string
  expense_id: string
  file_name: string
  file_url: string
  file_type: string
  file_size: number
  uploaded_at: string
}

export interface DocumentAnalysis {
  id: string
  expense_id?: string
  user_id: string
  original_filename: string
  file_url?: string
  file_type: string
  analysis_status: string
  extracted_data?: Record<string, any>
  confidence_score?: number
  needs_review: boolean
  processing_started_at?: string
  processing_completed_at?: string
  error_message?: string
  created_at: string
  updated_at?: string
}

export interface QuickSearchResult {
  id: string
  description: string
  total_amount: number
  expense_date: string
  expense_type: ExpenseType
}