"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { format } from "date-fns"
import { Plus, Search, UserPlus, Loader2, ChevronDown } from "lucide-react"
import { Tabs, TabsList, TabsContent, TabsTrigger } from "@/components/ui/tabs"
import { CreateExpensePayload, ExpenseType, PaymentMethod } from "@/lib/types/expenses"
import { Category } from "@/lib/types/settings"
import { Contact, ContactType } from "@/lib/types/contacts"
import { settingsApi } from "@/lib/api/settings"
import { searchVendorsAndSuppliers } from "@/lib/api/contacts"
import { useAuth } from "@/lib/contexts/AuthContext"
import { UUID } from "crypto"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils/utils"
import { CalendarIcon } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"

const paymentMethods = Object.values(PaymentMethod).map(method => ({
  value: method,
  label: method.replace(/_/g, ' ').toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}))

interface AddExpenseDialogProps {
  onAddExpense: (expense: CreateExpensePayload) => Promise<void>
}

export function AddExpenseDialog({ onAddExpense }: AddExpenseDialogProps) {
  const [open, setOpen] = useState(false)
  const [expenseType, setExpenseType] = useState<ExpenseType>(ExpenseType.simple)
  
  // Form data
  const [description, setDescription] = useState("")
  const [expenseDate, setExpenseDate] = useState<Date>(new Date())
  const [dueDate, setDueDate] = useState<Date | undefined>(undefined)
  const [invoiceNumber, setInvoiceNumber] = useState("")
  const [baseAmount, setBaseAmount] = useState("")
  const [taxAmount, setTaxAmount] = useState("")
  const [totalAmount, setTotalAmount] = useState("")
  const [notes, setNotes] = useState("")
  const [tags, setTags] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string>("")
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>("")
  const [selectedContact, setSelectedContact] = useState<string>("")
  
  // Data from API
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)
  
  // Contact search states
  const [contactSearchOpen, setContactSearchOpen] = useState(false)
  const [contactSearchValue, setContactSearchValue] = useState("")
  const [searchedContacts, setSearchedContacts] = useState<Contact[]>([])
  const [contactSearchLoading, setContactSearchLoading] = useState(false)
  
  // Popover states
  const [datePopoverOpen, setDatePopoverOpen] = useState(false)
  const [dueDatePopoverOpen, setDueDatePopoverOpen] = useState(false)
  
  const { token } = useAuth()

  // Calculate total amount for invoice
  const calculatedTotal = expenseType === ExpenseType.invoice 
    ? (Number(baseAmount) || 0) + (Number(taxAmount) || 0)
    : Number(totalAmount) || 0

  // Debounced search for contacts
  const searchContacts = useCallback(
    async (searchTerm: string) => {
      setContactSearchLoading(true)
      try {
        const contacts = await searchVendorsAndSuppliers(searchTerm, 10)
        setSearchedContacts(contacts)
      } catch (error) {
        console.error('Failed to search contacts:', error)
        setSearchedContacts([])
      } finally {
        setContactSearchLoading(false)
      }
    },
    []
  )

  // Debounce the search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchContacts(contactSearchValue)
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [contactSearchValue, searchContacts])

  // Fetch data on component mount
  useEffect(() => {
    if (open) {
      fetchData()
    }
  }, [open])

  const fetchData = async () => {
    setLoading(true)
    try {
      // Fetch categories
      const categoriesData = await settingsApi.categories.getCategories()
      const expenseCategories = categoriesData.filter(cat => cat.type === 'expense')
      setCategories(expenseCategories)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    
    if (!description.trim()) {
      // TODO: Show error toast
      return
    }

    if (!selectedCategory) {
      // TODO: Show error toast
      return
    }

    if (expenseType === ExpenseType.simple && !selectedPaymentMethod) {
      // TODO: Show error toast
      return
    }

    if (expenseType === ExpenseType.invoice && !selectedContact) {
      // TODO: Show error toast
      return
    }

    const amount = expenseType === ExpenseType.simple 
      ? Number(totalAmount) 
      : calculatedTotal

    if (isNaN(amount) || amount <= 0) {
      // TODO: Show error toast
      return
    }

    const expense: CreateExpensePayload = {
      description: description.trim(),
      expense_date: format(expenseDate, 'yyyy-MM-dd'),
      category_id: selectedCategory as UUID,
      payment_method: selectedPaymentMethod as PaymentMethod,
      total_amount: amount,
      notes: notes.trim() || undefined,
      currency: 'EUR',
      tags: tags.trim() ? tags.split(',').map(tag => tag.trim()).filter(Boolean) : undefined,
      expense_type: expenseType,
      custom_fields: {
        // Contact for both types
        ...(selectedContact && {
          contact_id: selectedContact,
        }),
        // Invoice-specific fields
        ...(expenseType === ExpenseType.invoice && {
          invoice_number: invoiceNumber.trim(),
          payment_due_date: dueDate ? format(dueDate, 'yyyy-MM-dd') : undefined,
          base_amount: baseAmount,
          tax_amount: taxAmount,
        })
      }
    }

    try {
      await onAddExpense(expense)
      setOpen(false)
      resetForm()
    } catch (error) {
      console.error('Failed to add expense:', error)
      // TODO: Show error toast
    }
  }

  const resetForm = () => {
    setDescription("")
    setExpenseDate(new Date())
    setDueDate(undefined)
    setInvoiceNumber("")
    setBaseAmount("")
    setTaxAmount("")
    setTotalAmount("")
    setNotes("")
    setTags("")
    setSelectedCategory("")
    setSelectedPaymentMethod("")
    setSelectedContact("")
    setContactSearchValue("")
    setSearchedContacts([])
  }

  const handleDateSelect = (newDate: Date | undefined) => {
    if (newDate) {
      setExpenseDate(newDate)
      setDatePopoverOpen(false)
    }
  }

  const handleDueDateSelect = (newDate: Date | undefined) => {
    if (newDate) {
      setDueDate(newDate)
      setDueDatePopoverOpen(false)
    }
  }

  const getSelectedContactName = () => {
    const contact = searchedContacts.find(c => c.id === selectedContact)
    return contact?.name || ""
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Expense
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-[800px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add New Expense</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Expense Type Tabs */}
          <Tabs value={expenseType} onValueChange={(value) => setExpenseType(value as ExpenseType)}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value={ExpenseType.simple}>Ticket</TabsTrigger>
              <TabsTrigger value={ExpenseType.invoice}>Invoice</TabsTrigger>
            </TabsList>
          </Tabs>

          {expenseType === ExpenseType.simple ? (
            // TICKET LAYOUT
            <div className="space-y-4">
              {/* Description */}
              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Input 
                  id="description" 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter expense description"
                  required 
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Date */}
                <div className="space-y-2">
                  <Label>Date *</Label>
                  <Popover open={datePopoverOpen} onOpenChange={setDatePopoverOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !expenseDate && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {expenseDate ? format(expenseDate, "PPP") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" style={{ zIndex: 9999 }}>
                      <Calendar
                        mode="single"
                        selected={expenseDate}
                        onSelect={handleDateSelect}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Category */}
                <div className="space-y-2">
                  <Label>Category *</Label>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory} required>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent style={{ zIndex: 9999 }}>
                      {categories.map((category) => (
                        <SelectItem key={category.id} value={category.id}>
                          {category.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Contact */}
                <div className="space-y-2">
                  <Label>Contact</Label>
                  <Popover open={contactSearchOpen} onOpenChange={setContactSearchOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={contactSearchOpen}
                        className="w-full justify-between"
                      >
                        {selectedContact ? getSelectedContactName() : "Search vendors/suppliers..."}
                        <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-[400px] p-0" style={{ zIndex: 9999 }}>
                      <Command>
                        <CommandInput 
                          placeholder="Search vendors and suppliers..." 
                          value={contactSearchValue}
                          onValueChange={setContactSearchValue}
                        />
                        <CommandList>
                          <CommandEmpty>
                            {contactSearchLoading ? (
                              <div className="flex items-center justify-center py-6">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span className="ml-2">Searching...</span>
                              </div>
                            ) : (
                              "No vendors/suppliers found."
                            )}
                          </CommandEmpty>
                          <CommandGroup>
                            {searchedContacts.map((contact) => (
                              <CommandItem
                                key={contact.id}
                                value={contact.id}
                                onSelect={() => {
                                  setSelectedContact(contact.id)
                                  setContactSearchOpen(false)
                                }}
                              >
                                <div className="flex flex-col">
                                  <span className="font-medium">{contact.name}</span>
                                  <span className="text-xs text-muted-foreground">
                                    {contact.contact_type} • {contact.city || 'No city'}
                                  </span>
                                </div>
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Payment Method */}
                <div className="space-y-2">
                  <Label>Payment Method *</Label>
                  <Select value={selectedPaymentMethod} onValueChange={setSelectedPaymentMethod} required>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select payment method" />
                    </SelectTrigger>
                    <SelectContent style={{ zIndex: 9999 }}>
                      {paymentMethods.map((method) => (
                        <SelectItem key={method.value} value={method.value}>
                          {method.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Total Amount */}
                <div className="space-y-2">
                  <Label htmlFor="totalAmount">Total Amount *</Label>
                  <Input 
                    id="totalAmount" 
                    type="number" 
                    step="0.01" 
                    value={totalAmount}
                    onChange={(e) => setTotalAmount(e.target.value)}
                    placeholder="0.00"
                    required 
                  />
                </div>

                {/* Tags */}
                <div className="space-y-2">
                  <Label htmlFor="tags">Tags</Label>
                  <Input 
                    id="tags" 
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                    placeholder="office, supplies, etc"
                  />
                </div>
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea 
                  id="notes" 
                  value={notes}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNotes(e.target.value)}
                  placeholder="Additional notes"
                  rows={3}
                />
              </div>
            </div>
          ) : (
            // INVOICE LAYOUT
            <div className="space-y-4">
              {/* Row 1: Contact and Date */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Contact *</Label>
                  <Popover open={contactSearchOpen} onOpenChange={setContactSearchOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={contactSearchOpen}
                        className="w-full justify-between"
                      >
                        {selectedContact ? getSelectedContactName() : "Search vendors/suppliers..."}
                        <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-[400px] p-0" style={{ zIndex: 9999 }}>
                      <Command>
                        <CommandInput 
                          placeholder="Search vendors and suppliers..." 
                          value={contactSearchValue}
                          onValueChange={setContactSearchValue}
                        />
                        <CommandList>
                          <CommandEmpty>
                            {contactSearchLoading ? (
                              <div className="flex items-center justify-center py-6">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span className="ml-2">Searching...</span>
                              </div>
                            ) : (
                              "No vendors/suppliers found."
                            )}
                          </CommandEmpty>
                          <CommandGroup>
                            {searchedContacts.map((contact) => (
                              <CommandItem
                                key={contact.id}
                                value={contact.id}
                                onSelect={() => {
                                  setSelectedContact(contact.id)
                                  setContactSearchOpen(false)
                                }}
                              >
                                <div className="flex flex-col">
                                  <span className="font-medium">{contact.name}</span>
                                  <span className="text-xs text-muted-foreground">
                                    {contact.contact_type} • {contact.city || 'No city'}
                                  </span>
                                </div>
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                </div>

                <div className="space-y-2">
                  <Label>Invoice Date *</Label>
                  <Popover open={datePopoverOpen} onOpenChange={setDatePopoverOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !expenseDate && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {expenseDate ? format(expenseDate, "PPP") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" style={{ zIndex: 9999 }}>
                      <Calendar
                        mode="single"
                        selected={expenseDate}
                        onSelect={handleDateSelect}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              {/* Row 2: Description */}
              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Input 
                  id="description" 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter expense description"
                  required 
                />
              </div>

              {/* Row 3: Invoice Number and Due Date */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="invoiceNumber">Invoice Number</Label>
                  <Input 
                    id="invoiceNumber" 
                    value={invoiceNumber}
                    onChange={(e) => setInvoiceNumber(e.target.value)}
                    placeholder="Enter invoice number"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Due Date</Label>
                  <Popover open={dueDatePopoverOpen} onOpenChange={setDueDatePopoverOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !dueDate && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {dueDate ? format(dueDate, "PPP") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" style={{ zIndex: 9999 }}>
                      <Calendar
                        mode="single"
                        selected={dueDate}
                        onSelect={handleDueDateSelect}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              {/* Row 4: Base Amount, Tax Amount, and Total Amount */}
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="baseAmount">Base Amount *</Label>
                  <Input 
                    id="baseAmount" 
                    type="number" 
                    step="0.01" 
                    value={baseAmount}
                    onChange={(e) => setBaseAmount(e.target.value)}
                    placeholder="0.00"
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="taxAmount">Tax Amount *</Label>
                  <Input 
                    id="taxAmount" 
                    type="number" 
                    step="0.01" 
                    value={taxAmount}
                    onChange={(e) => setTaxAmount(e.target.value)}
                    placeholder="0.00"
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="totalAmount">Total Amount</Label>
                  <Input 
                    id="totalAmount" 
                    type="number" 
                    step="0.01" 
                    value={calculatedTotal.toFixed(2)}
                    disabled
                    className="bg-muted"
                  />
                </div>
              </div>

              {/* Row 5: Category and Tags */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Category *</Label>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory} required>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent style={{ zIndex: 9999 }}>
                      {categories.map((category) => (
                        <SelectItem key={category.id} value={category.id}>
                          {category.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tags">Tags</Label>
                  <Input 
                    id="tags" 
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                    placeholder="office, supplies, etc"
                  />
                </div>
              </div>

              {/* Row 6: Notes */}
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea 
                  id="notes" 
                  value={notes}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNotes(e.target.value)}
                  placeholder="Additional notes"
                  rows={3}
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Adding..." : "Add Expense"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
} 