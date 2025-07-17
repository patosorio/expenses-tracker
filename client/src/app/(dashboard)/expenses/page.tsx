"use client"

import { useState } from "react"
import { ExpenseFilters } from "@/components/expenses/ExpenseFilters"
import { ExpenseList } from "@/components/expenses/ExpenseList"
import { AddExpenseDialog } from "@/components/expenses/AddExpenseDialog"
import { useToast } from "@/components/ui/use-toast"
import type { Expense, ExpenseFilters as ExpenseFiltersType } from "@/lib/types/expenses"
import { PaymentStatus } from "@/lib/types/expenses"
import { getExpenses, createExpense, updateExpense, deleteExpense, markExpensePaid } from "@/lib/api/expenses"
import { useEffect } from "react"

export default function ExpensesPage() {
  const [filters, setFilters] = useState<ExpenseFiltersType>({})
  const [searchTerm, setSearchTerm] = useState("")
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const { toast } = useToast()

  const fetchExpenses = async () => {
    try {
      setLoading(true)
      const response = await getExpenses(page, 10, {
        ...filters,
        search: searchTerm
      })
      setExpenses(response.expenses)
    } catch (error) {
      console.error("Failed to fetch expenses:", error)
      toast({
        title: "Error",
        description: "Failed to fetch expenses. Please try again.",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchExpenses()
  }, [page, filters, searchTerm])

  const handleAddExpense = async (data: any) => {
    try {
      await createExpense(data)
      toast({
        title: "Success",
        description: "Expense added successfully",
      })
      fetchExpenses()
    } catch (error) {
      console.error("Failed to add expense:", error)
      toast({
        title: "Error",
        description: "Failed to add expense. Please try again.",
        variant: "destructive"
      })
    }
  }

  const handleTogglePaid = async (id: string, isPaid: boolean) => {
    try {
      if (isPaid) {
        await updateExpense(id as any, { payment_status: PaymentStatus.PENDING })
      } else {
        await markExpensePaid(id as any)
      }
      toast({
        title: "Success",
        description: `Expense marked as ${isPaid ? "unpaid" : "paid"}`,
      })
      fetchExpenses()
    } catch (error) {
      console.error("Failed to update expense:", error)
      toast({
        title: "Error",
        description: "Failed to update expense. Please try again.",
        variant: "destructive"
      })
    }
  }

  const handleDeleteExpense = async (id: string) => {
    if (confirm("Are you sure you want to delete this expense?")) {
      try {
        await deleteExpense(id as any)
        toast({
          title: "Success",
          description: "Expense deleted successfully",
        })
        fetchExpenses()
      } catch (error) {
        console.error("Failed to delete expense:", error)
        toast({
          title: "Error",
          description: "Failed to delete expense. Please try again.",
          variant: "destructive"
        })
      }
    }
  }

  const handleEditExpense = (expense: Expense) => {
    // TODO: Implement edit functionality
    console.log("Edit expense:", expense)
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-light">Expenses</h1>
          <p className="text-muted-foreground text-sm">Manage your expenses</p>
        </div>
        <AddExpenseDialog onAddExpense={handleAddExpense} />
      </div>

      <ExpenseFilters
        filters={filters}
        onFiltersChange={setFilters}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
      />

      <ExpenseList
        expenses={expenses}
        loading={loading}
        onTogglePaid={handleTogglePaid}
        onDelete={handleDeleteExpense}
        onEdit={handleEditExpense}
      />
    </div>
  )
}
