"use client"

import { useParams } from "next/navigation"
import { useExpenseDetails } from "@/lib/hooks/expenses"
import { ExpenseDetailView } from "@/components/expenses"

export default function ExpensePage() {
  const params = useParams()
  const { data: expense, isLoading, error } = useExpenseDetails(params.id as string)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-muted rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="h-64 bg-muted rounded"></div>
              <div className="h-48 bg-muted rounded"></div>
            </div>
            <div className="space-y-6">
              <div className="h-32 bg-muted rounded"></div>
              <div className="h-24 bg-muted rounded"></div>
              <div className="h-32 bg-muted rounded"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !expense) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="space-y-4">
            <div className="text-lg font-light text-muted-foreground">
              {error ? 'Failed to load expense' : 'Expense not found'}
            </div>
            <p className="text-sm text-muted-foreground">
              {error ? String(error) : "The expense you're looking for doesn't exist or has been removed."}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return <ExpenseDetailView expense={expense} />
}
