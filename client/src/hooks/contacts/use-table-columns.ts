'use client'

import { useState, useCallback, useMemo } from 'react'
import { Contact, ContactType, TableColumn } from '@/types/contacts'

const DEFAULT_COLUMNS: TableColumn[] = [
  { 
    key: 'name', 
    label: 'Name', 
    sortable: true,
    hidden: false
  },
  { 
    key: 'contact_type', 
    label: 'Type', 
    sortable: true,
    hidden: false
  },
  { 
    key: 'email', 
    label: 'Email', 
    sortable: true,
    hidden: false
  },
  { 
    key: 'phone', 
    label: 'Phone', 
    sortable: false,
    hidden: false
  },
  { 
    key: 'country', 
    label: 'Country', 
    sortable: true,
    hidden: false
  },
  { 
    key: 'created_at', 
    label: 'Created', 
    sortable: true,
    hidden: false
  },
  // Additional available columns (hidden by default)
  { 
    key: 'tax_number', 
    label: 'Tax Number', 
    sortable: false,
    hidden: true
  },
  { 
    key: 'website', 
    label: 'Website', 
    sortable: false,
    hidden: true
  },
  { 
    key: 'city', 
    label: 'City', 
    sortable: true,
    hidden: true
  },
  { 
    key: 'state_province', 
    label: 'State/Province', 
    sortable: true,
    hidden: true
  },
  { 
    key: 'postal_code', 
    label: 'Postal Code', 
    sortable: false,
    hidden: true
  },
  { 
    key: 'full_address', 
    label: 'Full Address', 
    sortable: false,
    hidden: true
  },
  { 
    key: 'notes', 
    label: 'Notes', 
    sortable: false,
    hidden: true
  },
  { 
    key: 'updated_at', 
    label: 'Updated', 
    sortable: true,
    hidden: true
  }
]

interface UseTableColumnsReturn {
  columns: TableColumn[]
  visibleColumns: TableColumn[]
  toggleColumn: (columnKey: keyof Contact) => void
  resetColumns: () => void
  isColumnVisible: (columnKey: keyof Contact) => boolean
}

export const useTableColumns = (): UseTableColumnsReturn => {
  const [columns, setColumns] = useState<TableColumn[]>(DEFAULT_COLUMNS)

  const visibleColumns = useMemo(() => {
    return columns.filter(col => !col.hidden)
  }, [columns])

  const toggleColumn = useCallback((columnKey: keyof Contact) => {
    setColumns(prev => 
      prev.map(col => 
        col.key === columnKey 
          ? { ...col, hidden: !col.hidden }
          : col
      )
    )
  }, [])

  const resetColumns = useCallback(() => {
    setColumns(DEFAULT_COLUMNS)
  }, [])

  const isColumnVisible = useCallback((columnKey: keyof Contact) => {
    const column = columns.find(col => col.key === columnKey)
    return column ? !column.hidden : false
  }, [columns])

  return {
    columns,
    visibleColumns,
    toggleColumn,
    resetColumns,
    isColumnVisible
  }
}

// Helper function to get display value for a column
export const getColumnDisplayValue = (
  value: any, 
  contact: Contact, 
  columnKey: keyof Contact
): string => {
  if (value === null || value === undefined) {
    return '-'
  }

  switch (columnKey) {
    case 'contact_type':
      return value as ContactType
    case 'created_at':
    case 'updated_at':
      return new Date(value).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    case 'email':
      return value || '-'
    case 'phone':
      return value || '-'
    case 'website':
      return value || '-'
    case 'tags':
      return Array.isArray(value) ? value.join(', ') : '-'
    case 'full_address':
      return value || 'No address'
    default:
      return String(value)
  }
}

// Helper function to get contact type badge variant
export const getContactTypeBadgeVariant = (type: ContactType) => {
  switch (type) {
    case ContactType.CLIENT:
      return 'bg-blue-50 text-blue-700 border-blue-200'
    case ContactType.VENDOR:
      return 'bg-green-50 text-green-700 border-green-200'
    case ContactType.SUPPLIER:
      return 'bg-purple-50 text-purple-700 border-purple-200'
    default:
      return 'bg-gray-50 text-gray-700 border-gray-200'
  }
} 