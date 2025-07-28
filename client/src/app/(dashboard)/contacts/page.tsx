'use client'

import { useState, useCallback } from 'react'
import { Users, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ContactsToolbar } from '@/components/contacts/ContactsToolBar'
import { ContactsTable } from '@/components/contacts/ContactsTable'
import { ContactsPagination } from '@/components/contacts/ContactsPagination'
import { useContacts, useCreateContact, useDeleteContact, useUpdateContact } from '@/lib/hooks/contacts'
import { useTableColumns } from '@/lib/hooks/contacts/UseTableColumns'
import { Contact, ContactFilters } from '@/lib/types/contacts'
import { AddContactDialog } from '@/components/contacts/AddContactDialog'
import { EditContactDialog } from '@/components/contacts/EditContactDialog'

export default function ContactsPage() {
  const [pageSize, setPageSize] = useState(25)
  const [currentSort, setCurrentSort] = useState({ field: 'created_at', order: 'desc' as 'asc' | 'desc' })
  const [filters, setFilters] = useState<ContactFilters>({})
  const [editContact, setEditContact] = useState<Contact | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)

  // Table columns management
  const { columns, visibleColumns, toggleColumn, resetColumns } = useTableColumns()

  // Contacts data fetching with React Query
  const {
    contacts,
    total,
    pages,
    currentPage,
    isLoading,
    error,
    refetch,
    setPage,
    setFilters: updateFilters,
    setSort
  } = useContacts({
    page: 1,
    limit: pageSize,
    filters,
    sortBy: currentSort.field,
    sortOrder: currentSort.order
  })

  // Mutation hooks
  const createContact = useCreateContact()
  const deleteContact = useDeleteContact()
  const updateContact = useUpdateContact()

  // Check if any filters are active
  const hasActiveFilters = Boolean(
    filters.search || 
    filters.contact_type || 
    filters.country ||
    (filters.tags && filters.tags.length > 0)
  )

  // Handle filter changes
  const handleFiltersChange = useCallback((newFilters: ContactFilters) => {
    setFilters(newFilters)
    updateFilters(newFilters)
  }, [updateFilters])

  // Handle clear filters
  const handleClearFilters = useCallback(() => {
    const emptyFilters: ContactFilters = {}
    setFilters(emptyFilters)
    updateFilters(emptyFilters)
  }, [updateFilters])

  // Handle sorting
  const handleSort = useCallback((columnKey: keyof Contact) => {
    const newOrder = currentSort.field === columnKey && currentSort.order === 'asc' ? 'desc' : 'asc'
    setCurrentSort({ field: columnKey, order: newOrder })
    setSort(columnKey, newOrder)
  }, [currentSort, setSort])

  // Handle page size change
  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize)
    setPage(1) // Reset to first page when changing page size
  }, [setPage])

  // Handle contact actions
  const handleAddContact = useCallback(async (contactData: any) => {
    await createContact.mutateAsync(contactData)
  }, [createContact])

  const handleAddContactClick = useCallback(() => {
    // This is handled by the AddContactDialog component
  }, [])

  const handleViewContact = useCallback((contact: Contact) => {
    // TODO: Implement view contact modal/page
    console.log('View contact:', contact.name)
  }, [])

  const handleEditContact = useCallback((contact: Contact) => {
    setEditContact(contact)
    setEditDialogOpen(true)
  }, [])

  const handleDeleteContact = useCallback(async (contact: Contact) => {
    await deleteContact.mutateAsync(contact.id)
  }, [deleteContact])

  // Show error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-light">Contacts</h1>
            <p className="text-muted-foreground text-sm">Manage your clients, vendors, and suppliers</p>
          </div>
          <AddContactDialog onSuccess={refetch} />
        </div>
        <div className="text-center py-12">
          <div className="space-y-4">
            <div className="text-lg font-light text-muted-foreground">Failed to load contacts</div>
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
          <h1 className="text-2xl font-light">Contacts</h1>
          <p className="text-muted-foreground text-sm">Manage your clients, vendors, and suppliers</p>
        </div>
        <AddContactDialog onSuccess={refetch} />
      </div>

      {/* Toolbar */}
      <ContactsToolbar
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onClearFilters={handleClearFilters}
        columns={columns}
        onColumnToggle={toggleColumn}
        onColumnReset={resetColumns}
        totalContacts={total}
        hasActiveFilters={hasActiveFilters}
      />

      {/* Table */}
      <ContactsTable
        contacts={contacts}
        columns={visibleColumns}
        loading={isLoading}
        sortBy={currentSort.field}
        sortOrder={currentSort.order}
        onSort={handleSort}
        onView={handleViewContact}
        onEdit={handleEditContact}
        onDelete={handleDeleteContact}
      />

      {/* Pagination */}
      {total > 0 && (
        <ContactsPagination
          currentPage={currentPage}
          totalPages={pages}
          totalItems={total}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={handlePageSizeChange}
          loading={isLoading}
        />
      )}

      {/* Edit Contact Dialog */}
      <EditContactDialog
        contact={editContact}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        onContactUpdated={refetch}
      />
    </div>
  )
}
