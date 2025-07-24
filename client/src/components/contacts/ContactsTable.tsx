'use client'

import React from 'react'
import { MoreHorizontal, Eye, Edit, Trash2, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Contact, ContactType, TableColumn } from '@/lib/types/contacts'
import { ContactTypeBadge } from '@/components/contacts/ContactTypeBadge'
import { getColumnDisplayValue } from '@/hooks/contacts/UseTableColumns'

interface ContactsTableProps {
  contacts: Contact[]
  columns: TableColumn[]
  loading: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (columnKey: keyof Contact) => void
  onView?: (contact: Contact) => void
  onEdit?: (contact: Contact) => void
  onDelete?: (contact: Contact) => void
}

interface TableSkeletonProps {
  rows?: number
  columns?: number
}

const TableSkeleton = ({ rows = 10, columns = 6 }: TableSkeletonProps) => (
  <div className="space-y-4">
    {[...Array(rows)].map((_, i) => (
      <div key={i} className="flex space-x-4 py-3 border-b border-border">
        {[...Array(columns)].map((_, j) => (
          <div 
            key={j} 
            className={`h-4 bg-muted rounded animate-pulse ${
              j === 0 ? 'flex-1' : j === columns - 1 ? 'w-24' : 'w-32'
            }`} 
          />
        ))}
      </div>
    ))}
  </div>
)

export const ContactsTable = ({
  contacts,
  columns,
  loading,
  sortBy,
  sortOrder,
  onSort,
  onView,
  onEdit,
  onDelete
}: ContactsTableProps) => {
  const getSortIcon = (columnKey: keyof Contact) => {
    if (sortBy !== columnKey) {
      return <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
    }
    return sortOrder === 'asc' 
      ? <ArrowUp className="h-4 w-4 text-foreground" />
      : <ArrowDown className="h-4 w-4 text-foreground" />
  }

  const handleSort = (columnKey: keyof Contact, sortable?: boolean) => {
    if (sortable && onSort) {
      onSort(columnKey)
    }
  }

  const renderCellContent = (contact: Contact, column: TableColumn) => {
    const value = contact[column.key]
    
    if (column.key === 'contact_type') {
      return <ContactTypeBadge type={value as ContactType} />
    }
    
    if (column.key === 'email' && value) {
      return (
        <a 
          href={`mailto:${value}`} 
          className="text-primary hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {String(value)}
        </a>
      )
    }
    
    if (column.key === 'website' && value) {
      return (
        <a 
          href={value.toString().startsWith('http') ? value.toString() : `https://${value}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {String(value)}
        </a>
      )
    }
    
    return getColumnDisplayValue(value, contact, column.key)
  }

  if (loading) {
    return (
      <Card className="p-6">
        <TableSkeleton columns={columns.length + 1} />
      </Card>
    )
  }

  if (contacts.length === 0) {
    return (
      <Card className="p-12 text-center">
        <div className="space-y-4">
          <div className="text-lg font-light text-muted-foreground">No contacts found</div>
          <p className="text-sm text-muted-foreground">
            Try adjusting your search criteria or add a new contact
          </p>
        </div>
      </Card>
    )
  }

  return (
    <>
      {/* Desktop Table */}
      <div className="hidden md:block">
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  {columns.map((column) => (
                    <th 
                      key={column.key}
                      className={`px-4 py-3 text-left text-sm font-medium text-muted-foreground ${
                        column.sortable ? 'cursor-pointer hover:text-foreground transition-colors' : ''
                      }`}
                      onClick={() => handleSort(column.key, column.sortable)}
                    >
                      <div className="flex items-center gap-2">
                        {column.label}
                        {column.sortable && getSortIcon(column.key)}
                      </div>
                    </th>
                  ))}
                  <th className="px-4 py-3 w-12"></th>
                </tr>
              </thead>
              <tbody>
                {contacts.map((contact) => (
                  <tr
                    key={contact.id}
                    className="border-b border-border hover:bg-muted/20 transition-colors cursor-pointer"
                    onClick={() => onView?.(contact)}
                  >
                    {columns.map((column) => (
                      <td key={column.key} className="px-4 py-3 text-sm">
                        {renderCellContent(contact, column)}
                      </td>
                    ))}
                    <td className="px-4 py-3">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onView?.(contact)}>
                            <Eye className="h-4 w-4 mr-2" />
                            View
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onEdit?.(contact)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => onDelete?.(contact)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-4">
        {contacts.map((contact) => (
          <Card 
            key={contact.id} 
            className="p-4 cursor-pointer hover:bg-muted/20 transition-colors"
            onClick={() => onView?.(contact)}
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <h3 className="font-medium text-sm">{contact.name}</h3>
                  <div className="flex items-center gap-2">
                    <ContactTypeBadge type={contact.contact_type} />
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onView?.(contact)}>
                      <Eye className="h-4 w-4 mr-2" />
                      View
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEdit?.(contact)}>
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={() => onDelete?.(contact)}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              
              <div className="space-y-2 text-sm text-muted-foreground">
                {contact.email && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium w-16">Email:</span>
                    <a 
                      href={`mailto:${contact.email}`}
                      className="text-primary hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {contact.email}
                    </a>
                  </div>
                )}
                {contact.phone && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium w-16">Phone:</span>
                    <span>{contact.phone}</span>
                  </div>
                )}
                {contact.country && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium w-16">Country:</span>
                    <span>{contact.country}</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <span className="font-medium w-16">Created:</span>
                  <span>{new Date(contact.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </>
  )
} 