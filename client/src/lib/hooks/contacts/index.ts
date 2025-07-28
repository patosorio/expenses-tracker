import { useState, useCallback, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from '@/components/ui/use-toast'
import { contactsApi } from '@/lib/api/contacts'
import { 
  Contact,
  ContactFilters,
  ContactListResponse,
  CreateContactPayload,
  UpdateContactPayload,
  ContactSummaryResponse,
  UseContactsOptions,
  UseContactsReturn,
  ContactType
} from '@/lib/types/contacts'
import { errorHandlers } from '@/lib/errors/errorHandler'
import { useAuth } from '@/lib/contexts/AuthContext'

// Query keys for React Query
export const contactKeys = {
  all: ['contacts'] as const,
  lists: () => [...contactKeys.all, 'list'] as const,
  list: (filters: ContactFilters, page: number, limit: number, sortBy: string, sortOrder: string) => 
    [...contactKeys.lists(), { filters, page, limit, sortBy, sortOrder }] as const,
  details: () => [...contactKeys.all, 'detail'] as const,
  detail: (id: string) => [...contactKeys.details(), id] as const,
  summary: () => [...contactKeys.all, 'summary'] as const,
  search: (query: string) => [...contactKeys.all, 'search', query] as const,
}

/**
 * Hook for fetching paginated contacts with filters
 */
export const useContacts = (options: UseContactsOptions = {}): UseContactsReturn => {
  const {
    page = 1,
    limit = 25,
    filters = {},
    sortBy = 'created_at',
    sortOrder = 'desc',
    enabled = true
  } = options

  const [currentPage, setCurrentPage] = useState(page)
  const [currentFilters, setCurrentFilters] = useState<ContactFilters>(filters)
  const [currentSort, setCurrentSort] = useState({ sortBy, sortOrder })
  
  const { user, isLoading: authLoading } = useAuth()

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch: queryRefetch
  } = useQuery({
    queryKey: contactKeys.list(currentFilters, currentPage, limit, currentSort.sortBy, currentSort.sortOrder),
    queryFn: () => contactsApi.getContacts(
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

  const setFilters = useCallback((newFilters: ContactFilters) => {
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
    contacts: data?.contacts || [],
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
 * Hook for creating contacts
 */
export const useCreateContact = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (contactData: CreateContactPayload) => contactsApi.createContact(contactData),
    onSuccess: (newContact) => {
      // Invalidate ALL contact queries to ensure UI updates
      queryClient.invalidateQueries({ queryKey: contactKeys.all })

      toast({
        title: 'Success',
        description: 'Contact created successfully',
      })
    },
    onError: (error) => {
      errorHandlers.contacts.create(error)
    }
  })
}

/**
 * Hook for updating contacts
 */
export const useUpdateContact = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateContactPayload }) => 
      contactsApi.updateContact(id, data),
    onSuccess: (updatedContact) => {
      // Update cache with new data
      queryClient.setQueryData(
        contactKeys.detail(updatedContact.id),
        updatedContact
      )
      
      // Invalidate ALL contact queries to ensure UI updates
      queryClient.invalidateQueries({ queryKey: contactKeys.all })
      
      toast({
        title: 'Success',
        description: 'Contact updated successfully',
      })
    },
    onError: (error) => {
      errorHandlers.contacts.update(error)
    }
  })
}

/**
 * Hook for deleting contacts
 */
export const useDeleteContact = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => contactsApi.deleteContact(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: contactKeys.detail(deletedId) })
      
      // Invalidate ALL contact queries to ensure UI updates
      queryClient.invalidateQueries({ queryKey: contactKeys.all })
      
      toast({
        title: 'Success',
        description: 'Contact deleted successfully',
      })
    },
    onError: (error) => {
      errorHandlers.contacts.delete(error)
    }
  })
}

/**
 * Hook for fetching single contact details
 */
export const useContactDetails = (id: string) => {
  return useQuery({
    queryKey: contactKeys.detail(id),
    queryFn: () => contactsApi.getContactById(id),
    enabled: !!id,
    staleTime: 30000,
  })
}

/**
 * Hook for fetching contacts summary
 */
export const useContactsSummary = () => {
  return useQuery({
    queryKey: contactKeys.summary(),
    queryFn: () => contactsApi.getContactsSummary(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Hook for searching vendors and suppliers
 */
export const useSearchVendorsAndSuppliers = (searchTerm: string, limit: number = 10) => {
  const { user, isLoading: authLoading } = useAuth()

  return useQuery({
    queryKey: contactKeys.search(searchTerm),
    queryFn: () => contactsApi.searchVendorsAndSuppliers(searchTerm, limit),
    enabled: !authLoading && !!user && searchTerm.length >= 2,
    staleTime: 30000,
  })
}

/**
 * Hook for contact search with state management
 */
export const useContactSearch = (options: { 
  contactTypes?: ContactType[]
  enabled?: boolean 
} = {}) => {
  const { contactTypes = [ContactType.VENDOR, ContactType.SUPPLIER], enabled = true } = options
  const [searchQuery, setSearchQuery] = useState('')

  const { data: searchResults = [], isLoading: isSearching } = useQuery({
    queryKey: contactKeys.search(searchQuery),
    queryFn: () => contactsApi.searchVendorsAndSuppliers(searchQuery, 10),
    enabled: enabled && searchQuery.length >= 2,
    staleTime: 30000,
  })

  const searchContacts = useCallback((query: string) => {
    setSearchQuery(query.trim())
  }, [])

  const clearSearch = useCallback(() => {
    setSearchQuery('')
  }, [])

  return {
    searchContacts,
    clearSearch,
    searchResults,
    isSearching,
    searchQuery
  }
} 