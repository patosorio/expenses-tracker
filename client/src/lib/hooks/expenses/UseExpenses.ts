'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Expense,
  ExpenseFilters,
  PaginatedExpenseResponse,
  UseExpensesOptions,
  UseExpensesReturn } from '@/lib/types/expenses'
import { useApi } from '@/lib/hooks/UseApi'
import { expensesApi } from '@/lib/api/expenses'


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
  const isFetchingRef = useRef(false)

  const fetchExpenses = useCallback(async () => {
    if (!enabled || isFetchingRef.current) return

    try {
      isFetchingRef.current = true
      setIsLoading(true)
      setError(null)
      
      const response = await expensesApi.getExpenses(
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
      isFetchingRef.current = false
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
  }, [currentFilters.search, currentPage]) // eslint-disable-line react-hooks/exhaustive-deps

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