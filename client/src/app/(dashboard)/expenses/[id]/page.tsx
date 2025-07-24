"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { Expense } from "@/lib/types/expenses"
import { expensesApi } from "@/lib/api/expenses"
import { UUID } from "crypto"
import { ExpenseDetailView } from "@/components/expenses"

export default function ExpensePage() {
  const params = useParams()
  const [expense, setExpense] = useState<Expense | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchExpense = async () => {
      try {
        const data = await expensesApi.getExpenseById(params.id as UUID)
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

  if (!expense) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="space-y-4">
            <div className="text-lg font-light text-muted-foreground">Expense not found</div>
            <p className="text-sm text-muted-foreground">
              The expense you're looking for doesn't exist or has been removed.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return <ExpenseDetailView expense={expense} />
}
