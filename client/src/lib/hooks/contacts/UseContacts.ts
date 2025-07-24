'use client'

import { useState, useEffect, useCallback } from 'react'
import { Contact, ContactFilters, ContactListResponse } from '@/lib/types/contacts'
import { useApi } from '@/hooks/UseApi'
import { contactsApi } from '@/lib/api/contacts'

interface UseContactsOptions {
  page?: number
  limit?: number
  filters?: ContactFilters
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  enabled?: boolean
}

interface UseContactsReturn {
  contacts: Contact[]
  total: number
  pages: number
  currentPage: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  setPage: (page: number) => void
  setFilters: (filters: ContactFilters) => void
  setSort: (sortBy: string, sortOrder: 'asc' | 'desc') => void
}

export const useContacts = (options: UseContactsOptions = {}): UseContactsReturn => {
  const {
    page = 1,
    limit = 25,
    filters = {},
    sortBy = 'created_at',
    sortOrder = 'desc',
    enabled = true
  } = options

  const [data, setData] = useState<ContactListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(page)
  const [currentFilters, setCurrentFilters] = useState<ContactFilters>(filters)
  const [currentSort, setCurrentSort] = useState({ sortBy, sortOrder })

  const fetchContacts = useCallback(async () => {
    if (!enabled) return

    try {
      console.log('Fetching contacts with params:', {
        page: currentPage,
        limit,
        filters: currentFilters,
        sortBy: currentSort.sortBy,
        sortOrder: currentSort.sortOrder
      })
      setIsLoading(true)
      setError(null)
      
      const response = await contactsApi.getContacts(
        currentPage,
        limit,
        currentFilters,
        currentSort.sortBy,
        currentSort.sortOrder
      )
      
      console.log('Contacts fetched:', response.contacts.length, 'total:', response.total)
      setData(response)
    } catch (err) {
      console.error('Error fetching contacts:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch contacts')
    } finally {
      setIsLoading(false)
    }
  }, [enabled, currentPage, limit, currentFilters, currentSort])

  // Fetch data when dependencies change
  useEffect(() => {
    fetchContacts()
  }, [fetchContacts])

  // Debounce search filter
  useEffect(() => {
    if (!currentFilters.search) return

    const timeoutId = setTimeout(() => {
      if (currentPage !== 1) {
        setCurrentPage(1) // Reset to first page when searching
      } else {
        fetchContacts()
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [currentFilters.search]) // eslint-disable-line react-hooks/exhaustive-deps

  const setPage = useCallback((newPage: number) => {
    setCurrentPage(newPage)
  }, [])

  const setFilters = useCallback((newFilters: ContactFilters) => {
    setCurrentFilters(newFilters)
    setCurrentPage(1) // Reset to first page when filters change
  }, [])

  const setSort = useCallback((newSortBy: string, newSortOrder: 'asc' | 'desc') => {
    setCurrentSort({ sortBy: newSortBy, sortOrder: newSortOrder })
    setCurrentPage(1) // Reset to first page when sorting changes
  }, [])

  const refetch = useCallback(async () => {
    await fetchContacts()
  }, [fetchContacts])

  return {
    contacts: data?.contacts || [],
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