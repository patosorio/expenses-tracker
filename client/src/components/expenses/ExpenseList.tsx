import { Card, CardContent } from "@/components/ui/card"
import { ExpenseCard } from "./ExpenseCard"
import type { Expense } from "@/types/expenses"

interface ExpenseListProps {
  expenses: Expense[]
  loading: boolean
  onTogglePaid: (id: string, isPaid: boolean) => Promise<void>
  onDelete: (id: string) => Promise<void>
  onEdit: (expense: Expense) => void
}

export function ExpenseList({
  expenses,
  loading,
  onTogglePaid,
  onDelete,
  onEdit,
}: ExpenseListProps) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="animate-pulse space-y-2">
                <div className="h-4 bg-muted rounded w-1/4"></div>
                <div className="h-6 bg-muted rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (expenses.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">No expenses found</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {expenses.map((expense) => (
        <ExpenseCard
          key={expense.id.toString()}
          expense={expense}
          onTogglePaid={onTogglePaid}
          onDelete={onDelete}
          onEdit={onEdit}
        />
      ))}
    </div>
  )
} 