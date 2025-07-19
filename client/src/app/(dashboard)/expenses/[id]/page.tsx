"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { format } from "date-fns"
import { AlertCircle, ArrowLeft, Calendar, CreditCard, FileText, Receipt, Tag, User } from "lucide-react"
import { Expense, PaymentStatus } from "@/types/expenses"
import { getExpenseById } from "@/api/expenses"
import { UUID } from "crypto"

function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(amount)
}

function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const variants = {
    PAID: "bg-green-100 text-green-800",
    PENDING: "bg-yellow-100 text-yellow-800",
    CANCELLED: "bg-red-100 text-red-800",
    OVERDUE: "bg-red-100 text-red-800"
  }

  return (
    <Badge className={variants[status]} variant="outline">
      {status.toLowerCase()}
    </Badge>
  )
}

export default function ExpensePage() {
  const params = useParams()
  const router = useRouter()
  const [expense, setExpense] = useState<Expense | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchExpense = async () => {
      try {
        const data = await getExpenseById(params.id as UUID)
        setExpense(data)
      } catch (error) {
        console.error('Failed to fetch expense:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchExpense()
  }, [params.id])

  if (loading) {
    return <div className="animate-pulse">Loading...</div>
  }

  if (!expense) {
    return <div>Expense not found</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          <h1 className="text-2xl font-light">{expense.description}</h1>
        </div>
        <PaymentStatusBadge status={expense.payment_status} />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Main Information */}
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle className="text-lg font-light">Basic Information</CardTitle>
            <CardDescription>Primary details about this expense</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Amount Section */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium">Amount Details</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Base Amount</p>
                  <p className="text-lg">{formatCurrency(expense.base_amount, expense.currency)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Tax Amount</p>
                  <p className="text-lg">{formatCurrency(expense.tax_amount, expense.currency)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Amount</p>
                  <p className="text-lg font-medium">{formatCurrency(expense.total_amount, expense.currency)}</p>
                </div>
              </div>
            </div>

            <Separator />

            {/* Dates Section */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium">Important Dates</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Expense Date</p>
                    <p>{format(new Date(expense.expense_date), 'PPP')}</p>
                  </div>
                </div>
                {expense.payment_date && (
                  <div className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Payment Date</p>
                      <p>{format(new Date(expense.payment_date), 'PPP')}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <Separator />

            {/* Category and Payment Method */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium">Classification</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Category</p>
                  <p>{expense.category_id}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Payment Method</p>
                  <p>{expense.payment_method.toLowerCase().replace('_', ' ')}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Side Information */}
        <div className="space-y-6">
          {/* Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-light">Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Current Status</p>
                  <PaymentStatusBadge status={expense.payment_status} />
                </div>
                {expense.is_overdue && (
                  <div className="flex items-center gap-2 text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    <p className="text-sm">Overdue by {expense.days_overdue} days</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Tags Card */}
          {expense.tags && expense.tags.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-light">Tags</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {expense.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary">
                      <Tag className="h-3 w-3 mr-1" />
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Documents Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-light">Documents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {expense.receipt_url ? (
                  <div className="flex items-center gap-2">
                    <Receipt className="h-4 w-4 text-muted-foreground" />
                    <a 
                      href={expense.receipt_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      View Receipt
                    </a>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No documents attached</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Additional Details for Invoice Type */}
      {expense.expense_type === 'invoice' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-light">Invoice Details</CardTitle>
            <CardDescription>Additional information specific to this invoice</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium">Supplier Information</h3>
                <div className="mt-2 space-y-2">
                  <div>
                    <p className="text-sm text-muted-foreground">Supplier Name</p>
                    <p>{expense.supplier_name}</p>
                  </div>
                  {expense.supplier_tax_id && (
                    <div>
                      <p className="text-sm text-muted-foreground">Tax ID</p>
                      <p>{expense.supplier_tax_id}</p>
                    </div>
                  )}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium">Invoice Information</h3>
                <div className="mt-2 space-y-2">
                  {expense.invoice_number && (
                    <div>
                      <p className="text-sm text-muted-foreground">Invoice Number</p>
                      <p>{expense.invoice_number}</p>
                    </div>
                  )}
                  {expense.payment_due_date && (
                    <div>
                      <p className="text-sm text-muted-foreground">Due Date</p>
                      <p>{format(new Date(expense.payment_due_date), 'PPP')}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes Section */}
      {expense.notes && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-light">Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">{expense.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* Custom Fields */}
      {expense.custom_fields && Object.keys(expense.custom_fields).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-light">Additional Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(expense.custom_fields).map(([key, value]) => (
                <div key={key}>
                  <p className="text-sm text-muted-foreground">{key}</p>
                  <p className="text-sm">{JSON.stringify(value)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
