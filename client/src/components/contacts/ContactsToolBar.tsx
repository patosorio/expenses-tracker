'use client'

import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ContactFilters, ContactType, TableColumn } from '@/types/contacts'
import { Contact } from '@/types/contacts'
import { ColumnSelector } from './ColumnSelector'

interface ContactsToolbarProps {
  filters: ContactFilters
  onFiltersChange: (filters: ContactFilters) => void
  onClearFilters: () => void
  columns: TableColumn[]
  onColumnToggle: (columnKey: keyof Contact) => void
  onColumnReset: () => void
  totalContacts: number
  hasActiveFilters: boolean
}

export const ContactsToolbar = ({
  filters,
  onFiltersChange,
  onClearFilters,
  columns,
  onColumnToggle,
  onColumnReset,
  totalContacts,
  hasActiveFilters
}: ContactsToolbarProps) => {
  const handleSearchChange = (value: string) => {
    onFiltersChange({
      ...filters,
      search: value || undefined
    })
  }

  const handleTypeChange = (value: string) => {
    onFiltersChange({
      ...filters,
      contact_type: value === 'all' ? undefined : (value as ContactType)
    })
  }

  return (
    <div className="space-y-4">
      {/* Main toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          {/* Search */}
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search contacts..."
              value={filters.search || ''}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Type filter */}
          <Select 
            value={filters.contact_type || 'all'} 
            onValueChange={handleTypeChange}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value={ContactType.CLIENT}>Clients</SelectItem>
              <SelectItem value={ContactType.VENDOR}>Vendors</SelectItem>
              <SelectItem value={ContactType.SUPPLIER}>Suppliers</SelectItem>
            </SelectContent>
          </Select>

          {/* Clear filters */}
          {hasActiveFilters && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onClearFilters}
              className="text-muted-foreground"
            >
              <X className="h-4 w-4 mr-2" />
              Clear filters
            </Button>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <ColumnSelector 
            columns={columns} 
            onToggle={onColumnToggle} 
            onReset={onColumnReset}
          />
        </div>
      </div>

      {/* Results summary */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div>
          {totalContacts === 0 ? (
            'No contacts found'
          ) : totalContacts === 1 ? (
            '1 contact'
          ) : (
            `${totalContacts.toLocaleString()} contacts`
          )}
          {hasActiveFilters && ' (filtered)'}
        </div>
      </div>
    </div>
  )
}