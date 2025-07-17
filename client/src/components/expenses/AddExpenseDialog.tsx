"use client"

import React, { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { format } from "date-fns"
import { Plus, Upload } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsContent, TabsTrigger } from "@/components/ui/tabs"
import { CreateExpensePayload, ExpenseType, PaymentMethod, PaymentStatus } from "@/lib/types/expenses"
import { Category } from "@/lib/types/settings"
import { settingsApi } from "@/lib/api/settings"
import { useAuth } from "@/lib/contexts/AuthContext"
import { UUID } from "crypto"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils/utils"
import { CalendarIcon } from "lucide-react"

const recurringTypes = [
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "yearly", label: "Yearly" },
  { value: "weekly", label: "Weekly" },
  { value: "biweekly", label: "Bi-weekly" },
]

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
  const [date, setDate] = useState<Date>(new Date())
  const [dueDate, setDueDate] = useState<Date | undefined>(undefined)
  const [expenseType, setExpenseType] = useState<ExpenseType>(ExpenseType.simple)
  const [isPaid, setIsPaid] = useState(true)
  const [isRecurring, setIsRecurring] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>("")
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>("")
  const [recurringType, setRecurringType] = useState<string>("")
  const { token } = useAuth()

  // Fetch categories on component mount
  useEffect(() => {
    const fetchCategories = async () => {
      if (!token) {
        console.log('No token available')
        return
      }
      
      try {
        console.log('Fetching categories...')
        const data = await settingsApi.categories.getCategories()
        console.log('Categories received:', data)
        // Filter only expense categories
        const expenseCategories = data.filter(cat => cat.type === 'expense')
        console.log('Expense categories:', expenseCategories)
        setCategories(expenseCategories)
      } catch (error) {
        console.error('Failed to fetch categories:', error)
      }
    }

    if (open) {
      fetchCategories()
    }
  }, [token, open])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    
    const amount = Number(formData.get('amount'))
    if (isNaN(amount) || amount <= 0) {
      console.error('Invalid amount:', amount)
      // TODO: Show error toast
      return
    }

    const categoryId = selectedCategory
    if (!categoryId) {
      console.error('No category selected')
      // TODO: Show error toast
      return
    }

    const paymentMethod = selectedPaymentMethod
    if (!paymentMethod) {
      console.error('No payment method selected')
      // TODO: Show error toast
      return
    }

    const description = formData.get('description')?.toString().trim()
    if (!description) {
      console.error('No description provided')
      // TODO: Show error toast
      return
    }

    console.log('Form data:', {
      description,
      amount,
      categoryId,
      paymentMethod,
      date,
      tags: formData.get('tags')?.toString()
    })
    
    const expense: CreateExpensePayload = {
      description,
      expense_date: format(date, 'yyyy-MM-dd'),
      category_id: categoryId as UUID,
      payment_method: paymentMethod as PaymentMethod,
      total_amount: amount,
      notes: formData.get('notes')?.toString()?.trim(),
      currency: 'EUR',
      tags: formData.get('tags')?.toString()?.split(',').map(tag => tag.trim()).filter(Boolean),
      expense_type: expenseType,
      custom_fields: {
        supplier_name: formData.get('supplier')?.toString()?.trim(),
        supplier_address: formData.get('supplierAddress')?.toString()?.trim(),
        invoice_number: formData.get('invoiceNumber')?.toString()?.trim(),
        due_date: dueDate ? format(dueDate, 'yyyy-MM-dd') : undefined,
        is_recurring: isRecurring,
        recurring_type: isRecurring ? recurringType : undefined,
        recurring_day: isRecurring ? Number(formData.get('recurringDay')) : undefined,
        recurring_interval: isRecurring ? Number(formData.get('recurringInterval')) : undefined,
      }
    }

    try {
      console.log('Submitting expense:', expense)
      await onAddExpense(expense)
      setOpen(false)
      // Reset form
      setDate(new Date())
      setDueDate(undefined)
      setExpenseType(ExpenseType.simple)
      setIsPaid(true)
      setIsRecurring(false)
      setSelectedCategory("")
      setSelectedPaymentMethod("")
      setRecurringType("")
    } catch (error) {
      console.error('Failed to add expense:', error)
      // TODO: Show error toast
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Expense
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-[1000px] max-h-[85vh] overflow-y-auto z-50">
        <DialogHeader>
          <DialogTitle>Add New Expense</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="grid grid-cols-[3fr,2fr] gap-6">
          {/* Left Column - Form Fields */}
          <div className="space-y-4">
            {/* Tabs moved to left column */}
            <Tabs value={expenseType} onValueChange={(value) => {
              setExpenseType(value as ExpenseType)
              if (value === ExpenseType.simple) setIsPaid(true)
            }}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value={ExpenseType.simple}>Simple Expense</TabsTrigger>
                <TabsTrigger value={ExpenseType.invoice}>Invoice</TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="amount">Amount</Label>
                <Input id="amount" name="amount" type="number" step="0.01" required className="text-lg" />
              </div>
              {expenseType === ExpenseType.simple && (
                <div className="space-y-2">
                  <Label>Date</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !date && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, "PPP") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={date}
                        onSelect={(newDate) => newDate && setDate(newDate)}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              )}
            </div>

            {expenseType === ExpenseType.invoice && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Invoice Date</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !date && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, "PPP") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={date}
                        onSelect={(newDate) => newDate && setDate(newDate)}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
                <div className="space-y-2">
                  <Label>Due Date</Label>
                  <Popover>
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
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={dueDate}
                        onSelect={(newDate) => newDate && setDueDate(newDate)}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
            )}

            {/* {expenseType === ExpenseType.invoice && ()} */}

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input id="description" name="description" className="w-full" required />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Select value={selectedCategory} onValueChange={setSelectedCategory} required>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Payment Method</Label>
                <Select value={selectedPaymentMethod} onValueChange={setSelectedPaymentMethod} required>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select payment method" />
                  </SelectTrigger>
                  <SelectContent>
                    {paymentMethods.map((method) => (
                      <SelectItem key={method.value} value={method.value}>
                        {method.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {expenseType === ExpenseType.invoice && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Supplier Name</Label>
                    <Input name="supplier" required />
                  </div>
                  <div className="space-y-2">
                    <Label>Supplier Address</Label>
                    <Input name="supplierAddress" required />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Invoice Number</Label>
                  <Input name="invoiceNumber" required />
                </div>
              </>
            )}

            <div className="space-y-2">
              <Label>Notes</Label>
              <Input name="notes" />
            </div>

            <div className="space-y-2">
              <Label>Tags (comma separated)</Label>
              <Input name="tags" placeholder="office, supplies, etc" />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="isPaid" className="cursor-pointer">Mark as Paid</Label>
              <Switch 
                id="isPaid" 
                checked={isPaid} 
                onCheckedChange={setIsPaid} 
                disabled={expenseType === ExpenseType.simple} 
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="isRecurring" className="cursor-pointer">Recurring Expense</Label>
              <Switch id="isRecurring" checked={isRecurring} onCheckedChange={setIsRecurring} />
            </div>

            {isRecurring && (
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Recurring Type</Label>
                  <Select value={recurringType} onValueChange={setRecurringType} required>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {recurringTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Payment Day</Label>
                  <Input type="number" name="recurringDay" min="1" max="31" placeholder="Day of month" required />
                </div>
                <div className="space-y-2">
                  <Label>Interval</Label>
                  <Input type="number" name="recurringInterval" min="1" placeholder="Every X periods" required />
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Image Preview */}
          <div className="space-y-4">
            <Card className="border-dashed h-full">
              <CardContent className="p-6 flex flex-col items-center justify-center h-full space-y-6">
                <div className="p-4 rounded-full bg-muted">
                  <Upload className="h-8 w-8 text-muted-foreground" />
                </div>
                <div className="text-center space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Upload a document for automatic expense extraction
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Coming soon: AI-powered data extraction
                  </p>
                  <Button variant="outline" disabled size="sm" className="mt-2">
                    Upload Document
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="col-span-2 flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Add Expense</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
} 