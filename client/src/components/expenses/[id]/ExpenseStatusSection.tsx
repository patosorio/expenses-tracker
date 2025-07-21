'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, Clock, CheckCircle, XCircle } from 'lucide-react'
import { Expense, PaymentStatus } from '@/types/expenses'

interface ExpenseStatusSectionProps {
  expense: Expense
}

function getStatusIcon(status: PaymentStatus) {
  switch (status) {
    case 'PAID':
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case 'PENDING':
      return <Clock className="h-4 w-4 text-yellow-600" />
    case 'REFUNDED':
      return <XCircle className="h-4 w-4 text-red-600" />
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />
  }
}

function getStatusColor(status: PaymentStatus) {
  switch (status) {
    case 'PAID':
      return 'bg-green-100 text-green-800'
    case 'PENDING':
      return 'bg-yellow-100 text-yellow-800'
    case 'REFUNDED':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

export function ExpenseStatusSection({ expense }: ExpenseStatusSectionProps) {
  const isInvoice = expense.expense_type === 'INVOICE'
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-light">Status</CardTitle>
        <CardDescription>Current payment status and timeline</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Payment Status */}
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">Payment Status</p>
          <div className="flex items-center gap-2">
            {getStatusIcon(expense.payment_status)}
            <Badge className={getStatusColor(expense.payment_status)} variant="outline">
              {expense.payment_status.toLowerCase()}
            </Badge>
          </div>
        </div>

        {/* Overdue Information */}
        {isInvoice && expense.is_overdue && (
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <p className="text-sm font-medium">
              Overdue by {expense.days_overdue} days
            </p>
          </div>
        )}

        {/* Invoice-specific status */}
        {isInvoice && expense.payment_due_date && !expense.is_overdue && expense.payment_status === 'PENDING' && (
          <div className="flex items-center gap-2 text-blue-600">
            <Clock className="h-4 w-4" />
            <p className="text-sm">
              Due on {new Date(expense.payment_due_date).toLocaleDateString()}
            </p>
          </div>
        )}

        {/* Receipt-specific status */}
        {!isInvoice && expense.payment_status === 'PAID' && (
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle className="h-4 w-4" />
            <p className="text-sm">Paid immediately</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 