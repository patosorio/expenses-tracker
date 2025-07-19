import { MoreHorizontal, Edit, Trash2 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import type { Expense } from "@/types/expenses"
import { PaymentStatus } from "@/types/expenses"

interface ExpenseCardProps {
  expense: Expense
  onTogglePaid: (id: string, isPaid: boolean) => Promise<void>
  onDelete: (id: string) => Promise<void>
  onEdit: (expense: Expense) => void
}

export function ExpenseCard({
  expense,
  onTogglePaid,
  onDelete,
  onEdit,
}: ExpenseCardProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: expense.currency,
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  const isPaid = expense.payment_status === PaymentStatus.PAID

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <h3 className="font-medium">{expense.description}</h3>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <span>{formatDate(expense.expense_date)}</span>
                {expense.supplier_name && (
                  <>
                    <span>•</span>
                    <span>{expense.supplier_name}</span>
                  </>
                )}
                {expense.is_overdue && (
                  <>
                    <span>•</span>
                    <Badge variant="destructive" className="text-xs">
                      {expense.days_overdue} days overdue
                    </Badge>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="font-medium">{formatCurrency(expense.total_amount)}</p>
              <Badge 
                variant={
                  expense.payment_status === PaymentStatus.PAID 
                    ? "default" 
                    : expense.payment_status === PaymentStatus.OVERDUE
                    ? "destructive"
                    : "secondary"
                } 
                className="text-xs"
              >
                {expense.payment_status}
              </Badge>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onTogglePaid(expense.id.toString(), isPaid)}>
                  {isPaid ? "Mark as unpaid" : "Mark as paid"}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEdit(expense)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onDelete(expense.id.toString())} className="text-destructive">
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 