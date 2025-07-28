'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ExpensesToolbar } from '@/components/expenses/ExpensesToolbar'
import { ExpensesTable } from '@/components/expenses/ExpensesTable'
import { ExpensesPagination } from '@/components/expenses/ExpensesPagination'
import { AddExpenseDialog } from '@/components/expenses/AddExpenseDialog'
import { useTableColumns } from '@/lib/hooks/expenses/UseTableColumns'
import { 
  useExpenses, 
  useDeleteExpense, 
  useUpdateExpense 
} from '@/lib/hooks/expenses'
import { 
  Expense, 
  ExpenseFilters
} from '@/lib/types/expenses'

export default function ExpensesPage() {
  const router = useRouter()
  
  // UI State
  const [pageSize, setPageSize] = useState(25)
  const [currentSort, setCurrentSort] = useState({ 
    field: 'expense_date', 
    order: 'desc' as 'asc' | 'desc' 
  })
  const [filters, setFilters] = useState<ExpenseFilters>({})

  // Table columns management
  const { columns, visibleColumns, toggleColumn, resetColumns } = useTableColumns()

  // Business logic hooks - all API calls and state management handled here
  const {
    expenses,
    total,
    pages,
    currentPage,
    isLoading,
    error,
    refetch,
    setPage,
    setFilters: updateFilters,
    setSort
  } = useExpenses({
    page: 1,
    limit: pageSize,
    filters,
    sortBy: currentSort.field,
    sortOrder: currentSort.order
  })

  const deleteExpense = useDeleteExpense()
  const updateExpense = useUpdateExpense()

  // Derived state
  const hasActiveFilters = Boolean(
    filters.search || 
    filters.expense_type || 
    filters.payment_status ||
    filters.payment_method ||
    filters.min_amount ||
    filters.max_amount
  )

  // Event handlers - thin wrappers that delegate to hooks
  const handleFiltersChange = useCallback((newFilters: ExpenseFilters) => {
    setFilters(newFilters)
    updateFilters(newFilters)
  }, [updateFilters])

  const handleClearFilters = useCallback(() => {
    const emptyFilters: ExpenseFilters = {}
    setFilters(emptyFilters)
    updateFilters(emptyFilters)
  }, [updateFilters])

  const handleSort = useCallback((columnKey: keyof Expense) => {
    const newOrder = currentSort.field === columnKey && currentSort.order === 'asc' ? 'desc' : 'asc'
    setCurrentSort({ field: columnKey, order: newOrder })
    setSort(columnKey, newOrder)
  }, [currentSort, setSort])

  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize)
    setPage(1)
  }, [setPage])

  // Business operations - simple calls to hooks
  const handleViewExpense = useCallback((expense: Expense) => {
    router.push(`/expenses/${expense.id}`)
  }, [router])

  const handleEditExpense = useCallback((expense: Expense) => {
    // This would open edit modal or navigate to edit page
    // For now, just navigate to detail view
    router.push(`/expenses/${expense.id}`)
  }, [router])

  const handleDeleteExpense = useCallback(async (expense: Expense) => {
    if (confirm(`Are you sure you want to delete "${expense.description}"?`)) {
      deleteExpense.mutate(expense.id)
    }
  }, [deleteExpense])

  // Show error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-light">Expenses</h1>
            <p className="text-muted-foreground text-sm">Manage your expenses</p>
          </div>
          <AddExpenseDialog onSuccess={refetch} />
        </div>
        <div className="text-center py-12">
          <div className="space-y-4">
            <div className="text-lg font-light text-muted-foreground">Failed to load expenses</div>
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button variant="outline" onClick={refetch}>
              Try Again
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-light">Expenses</h1>
          <p className="text-muted-foreground text-sm">Manage your expenses</p>
        </div>
        <AddExpenseDialog onSuccess={refetch} />
      </div>

      {/* Toolbar */}
      <ExpensesToolbar
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onClearFilters={handleClearFilters}
        columns={columns}
        onColumnToggle={toggleColumn}
        onColumnReset={resetColumns}
        totalExpenses={total}
        hasActiveFilters={hasActiveFilters}
      />

      {/* Table */}
      <ExpensesTable
        expenses={expenses}
        columns={visibleColumns}
        loading={isLoading}
        sortBy={currentSort.field}
        sortOrder={currentSort.order}
        onSort={handleSort}
        onView={handleViewExpense}
        onEdit={handleEditExpense}
        onDelete={handleDeleteExpense}
      />

      {/* Pagination */}
      {total > 0 && (
        <ExpensesPagination
          currentPage={currentPage}
          totalPages={pages}
          totalItems={total}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={handlePageSizeChange}
          loading={isLoading}
        />
      )}
    </div>
  )
}