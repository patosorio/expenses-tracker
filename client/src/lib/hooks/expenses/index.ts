// client/src/lib/hooks/expenses/index.ts

import { useState, useCallback, useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from '@/components/ui/use-toast'
import { expensesApi } from '@/lib/api/expenses'
import { 
  CreateExpensePayload, 
  UpdateExpensePayload,
  Expense,
  PaginatedExpenseResponse,
  ExpenseFilters,
  ExpenseStats,
  BulkDeleteRequest,
  BulkUpdateRequest,
  UseExpensesOptions,
  UseExpensesReturn
} from '@/lib/types/expenses'
import { errorHandlers } from '@/lib/errors/errorHandler'
import { useAuth } from '@/lib/contexts/AuthContext'

// Query keys for React Query
export const expenseKeys = {
  all: ['expenses'] as const,
  lists: () => [...expenseKeys.all, 'list'] as const,
  list: (filters: ExpenseFilters, page: number, limit: number, sortBy: string, sortOrder: string) => 
    [...expenseKeys.lists(), { filters, page, limit, sortBy, sortOrder }] as const,
  details: () => [...expenseKeys.all, 'detail'] as const,
  detail: (id: string) => [...expenseKeys.details(), id] as const,
  stats: () => [...expenseKeys.all, 'stats'] as const,
  ocr: (analysisId: string) => [...expenseKeys.all, 'ocr', analysisId] as const,
}

/**
 * Hook for fetching paginated expenses with filters
 */
export const useExpenses = (options: UseExpensesOptions = {}): UseExpensesReturn => {
  const {
    page = 1,
    limit = 25,
    filters = {},
    sortBy = 'expense_date',
    sortOrder = 'desc',
    enabled = true
  } = options

  const [currentPage, setCurrentPage] = useState(page)
  const [currentFilters, setCurrentFilters] = useState<ExpenseFilters>(filters)
  const [currentSort, setCurrentSort] = useState({ sortBy, sortOrder })
  
  const { user, isLoading: authLoading } = useAuth()

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch: queryRefetch
  } = useQuery({
    queryKey: expenseKeys.list(currentFilters, currentPage, limit, currentSort.sortBy, currentSort.sortOrder),
    queryFn: () => expensesApi.getExpenses(
      currentPage,
      limit,
      currentFilters,
      currentSort.sortBy,
      currentSort.sortOrder
    ),
    enabled: enabled && !authLoading && !!user,
    staleTime: 30000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
  })

  // Handle search debouncing
  useEffect(() => {
    if (!currentFilters.search) return

    const timeoutId = setTimeout(() => {
      if (currentPage !== 1) {
        setCurrentPage(1)
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [currentFilters.search, currentPage])

  const setPage = useCallback((newPage: number) => {
    setCurrentPage(newPage)
  }, [])

  const setFilters = useCallback((newFilters: ExpenseFilters) => {
    setCurrentFilters(newFilters)
    setCurrentPage(1)
  }, [])

  const setSort = useCallback((newSortBy: string, newSortOrder: 'asc' | 'desc') => {
    setCurrentSort({ sortBy: newSortBy, sortOrder: newSortOrder })
    setCurrentPage(1)
  }, [])

  const refetch = useCallback(async () => {
    await queryRefetch()
  }, [queryRefetch])

  return {
    expenses: data?.expenses || [],
    total: data?.total || 0,
    pages: data?.pages || 0,
    currentPage,
    isLoading: isLoading || authLoading,
    error: error?.message || null,
    refetch,
    setPage,
    setFilters,
    setSort
  }
}

/**
 * Hook for creating expenses
 */
export const useCreateExpense = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (expenseData: CreateExpensePayload) => expensesApi.createExpense(expenseData),
    onSuccess: (newExpense) => {
      // Invalidate and refetch expenses list
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() })
      queryClient.invalidateQueries({ queryKey: expenseKeys.stats() })
      
      toast({
        title: 'Success',
        description: 'Expense created successfully',
      })
    },
    onError: (error) => {
      errorHandlers.expenses.create(error)
    }
  })
}

/**
 * Hook for updating expenses
 */
export const useUpdateExpense = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateExpensePayload }) => 
      expensesApi.updateExpense(id, data),
    onSuccess: (updatedExpense) => {
      // Update cache with new data
      queryClient.setQueryData(
        expenseKeys.detail(updatedExpense.id),
        updatedExpense
      )
      
      // Invalidate lists to show updated data
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() })
      queryClient.invalidateQueries({ queryKey: expenseKeys.stats() })
      
      toast({
        title: 'Success',
        description: 'Expense updated successfully',
      })
    },
    onError: (error) => {
      errorHandlers.expenses.update(error)
    }
  })
}

/**
 * Hook for deleting expenses
 */
export const useDeleteExpense = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => expensesApi.deleteExpense(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: expenseKeys.detail(deletedId) })
      
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() })
      queryClient.invalidateQueries({ queryKey: expenseKeys.stats() })
      
      toast({
        title: 'Success',
        description: 'Expense deleted successfully',
      })
    },
    onError: (error) => {
      errorHandlers.expenses.delete(error)
    }
  })
}

/**
 * Hook for marking expense as paid
 */
export const useMarkExpenseAsPaid = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, paymentDate }: { id: string; paymentDate?: string }) => 
      expensesApi.markExpenseAsPaid(id, paymentDate),
    onSuccess: (updatedExpense) => {
      // Update cache
      queryClient.setQueryData(
        expenseKeys.detail(updatedExpense.id),
        updatedExpense
      )
      
      // Invalidate lists and stats
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() })
      queryClient.invalidateQueries({ queryKey: expenseKeys.stats() })
      
      toast({
        title: 'Success',
        description: 'Expense marked as paid successfully',
      })
    },
    onError: (error) => {
      errorHandlers.expenses.markPaid(error)
    }
  })
}

/**
 * Hook for fetching expense statistics
 */
export const useExpenseStats = () => {
  return useQuery({
    queryKey: expenseKeys.stats(),
    queryFn: () => expensesApi.getExpenseStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Hook for bulk operations
 */
export const useBulkOperations = () => {
  const queryClient = useQueryClient()

  const bulkDelete = useMutation({
    mutationFn: (request: BulkDeleteRequest) => expensesApi.bulkDeleteExpenses(request),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() })
      queryClient.invalidateQueries({ queryKey: expenseKeys.stats() })
      
      toast({
        title: 'Success',
        description: `${response.deleted_count} expenses deleted successfully`,
      })
    },
    onError: (error) => {
      errorHandlers.expenses.delete(error)
    }
  })

  const bulkUpdate = useMutation({
    mutationFn: (request: BulkUpdateRequest) => expensesApi.bulkUpdateExpenses(request),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() })
      queryClient.invalidateQueries({ queryKey: expenseKeys.stats() })
      
      toast({
        title: 'Success',
        description: `${response.updated_count} expenses updated successfully`,
      })
    },
    onError: (error) => {
      errorHandlers.expenses.update(error)
    }
  })

  return {
    bulkDelete,
    bulkUpdate
  }
}

/**
 * Hook for OCR processing
 */
export const useOCRProcessing = () => {
  const queryClient = useQueryClient()

  const uploadReceipt = useMutation({
    mutationFn: ({ file, expenseId }: { file: File; expenseId?: string }) => 
      expensesApi.uploadReceiptForOCR(file, expenseId),
    onSuccess: (result) => {
      toast({
        title: 'Success',
        description: 'Receipt uploaded for processing',
      })
    },
    onError: (error) => {
      errorHandlers.expenses.create(error)
    }
  })

  const createFromOCR = useMutation({
    mutationFn: ({ analysisId, userCorrections }: { 
      analysisId: string; 
      userCorrections?: Record<string, any> 
    }) => expensesApi.createExpenseFromOCR(analysisId, userCorrections),
    onSuccess: (newExpense) => {
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() })
      queryClient.invalidateQueries({ queryKey: expenseKeys.stats() })
      
      toast({
        title: 'Success',
        description: 'Expense created from OCR analysis',
      })
    },
    onError: (error) => {
      errorHandlers.expenses.create(error)
    }
  })

  const getOCRAnalysis = (analysisId: string) => useQuery({
    queryKey: expenseKeys.ocr(analysisId),
    queryFn: () => expensesApi.getOCRAnalysis(analysisId),
    enabled: !!analysisId,
    refetchInterval: (data) => data ? false : 2000, // Poll every 2s until complete
  })

  return {
    uploadReceipt,
    createFromOCR,
    getOCRAnalysis
  }
}

/**
 * Hook for fetching single expense details
 */
export const useExpenseDetails = (id: string) => {
  return useQuery({
    queryKey: expenseKeys.detail(id),
    queryFn: () => expensesApi.getExpenseById(id),
    enabled: !!id,
    staleTime: 30000,
  })
}