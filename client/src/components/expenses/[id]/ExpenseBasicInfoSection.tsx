'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Calendar, Tag, User, Building2 } from 'lucide-react'
import { Expense } from '@/lib/types/expenses'

interface ExpenseBasicInfoSectionProps {
  expense: Expense
}

export function ExpenseBasicInfoSection({ expense }: ExpenseBasicInfoSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-light">Basic Information</CardTitle>
        <CardDescription>Primary details about this expense</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Dates Section */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium">Important Dates</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Expense Date</p>
                <p className="font-medium">
                  {new Date(expense.expense_date).toLocaleDateString()}
                </p>
              </div>
            </div>
            {expense.payment_date && (
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Payment Date</p>
                  <p className="font-medium">
                    {new Date(expense.payment_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <Separator />

        {/* Classification Section */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium">Classification</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Category</p>
              <p className="font-medium">Category ID: {expense.category_id}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Type</p>
              <p className="font-medium">
                {expense.expense_type === 'INVOICE' ? 'Invoice' : 'Receipt'}
              </p>
            </div>
          </div>
        </div>

        {/* Contact Information */}
        {expense.contact_id && (
          <>
            <Separator />
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Contact Information</h3>
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Contact</p>
                  <p className="font-medium">Contact ID: {expense.contact_id}</p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Notes */}
        {expense.notes && (
          <>
            <Separator />
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Notes</h3>
              <p className="text-sm whitespace-pre-wrap">{expense.notes}</p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
} 