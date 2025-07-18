'use client'

import { useState, useEffect, useCallback } from 'react'
import { 
  Expense, 
  ExpenseFilters, 
  PaginatedExpenseResponse 
} from '@/lib/types/expenses'
import { getExpenses } from '@/lib/api/expenses'

interface UseExpensesOptions {
  page?: number
  limit?: number
  filters?: ExpenseFilters
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  enabled?: boolean
}

interface UseExpensesReturn {
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

export const useExpenses = (options: UseExpensesOptions = {}): UseExpensesReturn => {
  const {
    page = 1,
    limit = 25,
    filters = {},
    sortBy = 'expense_date',
    sortOrder = 'desc',
    enabled = true
  } = options

  const [data, setData] = useState<PaginatedExpenseResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(page)
  const [currentFilters, setCurrentFilters] = useState<ExpenseFilters>(filters)
  const [currentSort, setCurrentSort] = useState({ sortBy, sortOrder })

  const fetchExpenses = useCallback(async () => {
    if (!enabled) return

    try {
      setIsLoading(true)
      setError(null)
      
      const response = await getExpenses(
        currentPage,
        limit,
        currentFilters,
        currentSort.sortBy,
        currentSort.sortOrder
      )
      
      setData(response)
    } catch (err) {
      console.error('Error fetching expenses:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch expenses')
    } finally {
      setIsLoading(false)
    }
  }, [enabled, currentPage, limit, currentFilters, currentSort])

  // Fetch data when dependencies change
  useEffect(() => {
    fetchExpenses()
  }, [fetchExpenses])

  // Debounce search filter
  useEffect(() => {
    if (!currentFilters.search) return

    const timeoutId = setTimeout(() => {
      if (currentPage !== 1) {
        setCurrentPage(1) // Reset to first page when searching
      } else {
        fetchExpenses()
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [currentFilters.search]) // eslint-disable-line react-hooks/exhaustive-deps

  const setPage = useCallback((newPage: number) => {
    setCurrentPage(newPage)
  }, [])

  const setFilters = useCallback((newFilters: ExpenseFilters) => {
    setCurrentFilters(newFilters)
    setCurrentPage(1) // Reset to first page when filters change
  }, [])

  const setSort = useCallback((newSortBy: string, newSortOrder: 'asc' | 'desc') => {
    setCurrentSort({ sortBy: newSortBy, sortOrder: newSortOrder })
    setCurrentPage(1) // Reset to first page when sorting changes
  }, [])

  const refetch = useCallback(async () => {
    await fetchExpenses()
  }, [fetchExpenses])

  return {
    expenses: data?.expenses || [],
    total: data?.total || 0,
    pages: data?.pages || 0,
    currentPage,
    isLoading,
    error,
    refetch,
    setPage,
    setFilters,
    setSort
  }
} 