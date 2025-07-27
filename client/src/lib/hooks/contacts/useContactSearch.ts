import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { contactsApi } from '@/lib/api/contacts'
import { Contact, ContactType } from '@/lib/types/contacts'

interface UseContactSearchOptions {
  contactTypes?: ContactType[]
  enabled?: boolean
}

export const useContactSearch = (options: UseContactSearchOptions = {}) => {
  const { contactTypes = ['VENDOR', 'SUPPLIER'], enabled = true } = options
  const [searchQuery, setSearchQuery] = useState('')

  const { data: searchResults = [], isLoading: isSearching } = useQuery({
    queryKey: ['contacts', 'search', searchQuery, contactTypes],
    queryFn: () => contactsApi.searchVendorsAndSuppliers(searchQuery, 10),
    enabled: enabled && searchQuery.length > 0,
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