'use client'

import { useState, useCallback } from 'react'
import { Receipt, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import { ExpensesToolbar } from '@/components/expenses/ExpensesToolbar'
import { ExpensesTable } from '@/components/expenses/ExpensesTable'
import { ExpensesPagination } from '@/components/expenses/expenses-pagination'
import { useExpenses } from '@/hooks/expenses/use-expenses'
import { useTableColumns } from '@/hooks/expenses/use-table-columns'
import { Expense, ExpenseFilters, CreateExpensePayload } from '@/types/expenses'
import { deleteExpense, createExpense, markExpensePaid } from '@/api/expenses'
import { AddExpenseDialog } from '@/components/expenses/AddExpenseDialog'

export default function ExpensesPage() {
  const { toast } = useToast()
  const [pageSize, setPageSize] = useState(25)
  const [currentSort, setCurrentSort] = useState({ field: 'expense_date', order: 'desc' as 'asc' | 'desc' })
  const [filters, setFilters] = useState<ExpenseFilters>({})

  // Table columns management
  const { columns, visibleColumns, toggleColumn, resetColumns } = useTableColumns()

  // Expenses data fetching
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

  // Check if any filters are active
  const hasActiveFilters = Boolean(
    filters.search || 
    filters.expense_type || 
    filters.payment_status ||
    filters.payment_method ||
    filters.min_amount ||
    filters.max_amount
  )

  // Handle filter changes
  const handleFiltersChange = useCallback((newFilters: ExpenseFilters) => {
    setFilters(newFilters)
    updateFilters(newFilters)
  }, [updateFilters])

  // Handle clear filters
  const handleClearFilters = useCallback(() => {
    const emptyFilters: ExpenseFilters = {}
    setFilters(emptyFilters)
    updateFilters(emptyFilters)
  }, [updateFilters])

  // Handle sorting
  const handleSort = useCallback((columnKey: keyof Expense) => {
    const newOrder = currentSort.field === columnKey && currentSort.order === 'asc' ? 'desc' : 'asc'
    setCurrentSort({ field: columnKey, order: newOrder })
    setSort(columnKey, newOrder)
  }, [currentSort, setSort])

  // Handle page size change
  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize)
    setPage(1) // Reset to first page when changing page size
  }, [setPage])

  // Handle expense actions
  const handleAddExpense = useCallback(async (expenseData: CreateExpensePayload) => {
    try {
      await createExpense(expenseData)
      refetch()
    } catch (error) {
      // Re-throw the error so the dialog can handle it
      throw error
    }
  }, [refetch])

  const handleViewExpense = useCallback((expense: Expense) => {
    // TODO: Implement view expense modal/page
    toast({
      title: "View Expense",
      description: `Viewing expense: ${expense.description}`,
    })
  }, [toast])

  const handleEditExpense = useCallback((expense: Expense) => {
    // TODO: Implement edit expense modal/page
    toast({
      title: "Edit Expense",
      description: `Editing expense: ${expense.description}`,
    })
  }, [toast])

  const handleDeleteExpense = useCallback(async (expense: Expense) => {
    try {
      await deleteExpense(expense.id)
      toast({
        title: "Expense Deleted",
        description: `${expense.description} has been deleted successfully.`,
      })
      refetch()
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to delete expense. Please try again.",
        variant: "destructive",
      })
    }
  }, [toast, refetch])

  // Show error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-light">Expenses</h1>
            <p className="text-muted-foreground text-sm">Manage your expenses</p>
          </div>
          <AddExpenseDialog onAddExpense={handleAddExpense} />
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
        <AddExpenseDialog onAddExpense={handleAddExpense} />
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
