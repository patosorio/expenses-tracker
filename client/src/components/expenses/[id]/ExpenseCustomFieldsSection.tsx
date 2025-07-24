'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Expense } from '@/lib/types/expenses'

interface ExpenseCustomFieldsSectionProps {
  expense: Expense
}

export function ExpenseCustomFieldsSection({ expense }: ExpenseCustomFieldsSectionProps) {
  if (!expense.custom_fields || Object.keys(expense.custom_fields).length === 0) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-light">Additional Information</CardTitle>
        <CardDescription>Custom fields and metadata</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(expense.custom_fields).map(([key, value]) => (
            <div key={key} className="space-y-1">
              <p className="text-sm text-muted-foreground capitalize">
                {key.replace(/_/g, ' ')}
              </p>
              <p className="text-sm font-medium">
                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
} 