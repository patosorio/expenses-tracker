'use client'

import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ExpenseStatusBadge } from '../ExpenseStatusBadge'
import { Expense, PaymentStatus } from '@/lib/types/expenses'
import { useRouter } from 'next/navigation'

interface ExpenseDetailHeaderProps {
  expense: Expense
}

export function ExpenseDetailHeader({ expense }: ExpenseDetailHeaderProps) {
  const router = useRouter()

  return (
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
        <div>
          <h1 className="text-2xl font-light">{expense.description}</h1>
          <p className="text-sm text-muted-foreground">
            {expense.expense_type === 'INVOICE' ? 'Invoice' : 'Receipt'} • {expense.currency}
          </p>
        </div>
      </div>
      <ExpenseStatusBadge status={expense.payment_status} />
    </div>
  )
} 