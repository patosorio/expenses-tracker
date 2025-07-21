'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Expense } from '@/types/expenses'

interface ExpenseAmountSectionProps {
  expense: Expense
}

function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(amount)
}

export function ExpenseAmountSection({ expense }: ExpenseAmountSectionProps) {
  const isInvoice = expense.expense_type === 'INVOICE'
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-light">Financial Details</CardTitle>
        <CardDescription>Amount breakdown and payment information</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Amount Breakdown */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium">Amount Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Base Amount</p>
              <p className="text-lg font-medium">
                {formatCurrency(expense.base_amount, expense.currency)}
              </p>
            </div>
            {isInvoice && (
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Tax Amount</p>
                <p className="text-lg">
                  {formatCurrency(expense.tax_amount, expense.currency)}
                </p>
              </div>
            )}
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Amount</p>
              <p className="text-xl font-semibold">
                {formatCurrency(expense.total_amount, expense.currency)}
              </p>
            </div>
          </div>
        </div>

        <Separator />

        {/* Payment Information */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium">Payment Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Payment Method</p>
              <p className="font-medium">
                {expense.payment_method?.toLowerCase().replace('_', ' ') || 'Not specified'}
              </p>
            </div>
            {expense.payment_date && (
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Payment Date</p>
                <p className="font-medium">
                  {new Date(expense.payment_date).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Invoice-specific information */}
        {isInvoice && expense.payment_due_date && (
          <>
            <Separator />
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Invoice Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {expense.invoice_number && (
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Invoice Number</p>
                    <p className="font-medium">{expense.invoice_number}</p>
                  </div>
                )}
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Due Date</p>
                  <p className="font-medium">
                    {new Date(expense.payment_due_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
} 