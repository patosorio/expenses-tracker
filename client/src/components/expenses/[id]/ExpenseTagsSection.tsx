'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tag } from 'lucide-react'
import { Expense } from '@/lib/types/expenses'

interface ExpenseTagsSectionProps {
  expense: Expense
}

export function ExpenseTagsSection({ expense }: ExpenseTagsSectionProps) {
  if (!expense.tags || expense.tags.length === 0) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-light">Tags</CardTitle>
        <CardDescription>Labels and categories for this expense</CardDescription>
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
  )
} 