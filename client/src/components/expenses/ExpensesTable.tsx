'use client'

import React from 'react'
import { MoreHorizontal, Eye, Edit, Trash2, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Expense } from '@/lib/types/expenses'
import { TableColumn } from '@/lib/hooks/expenses/UseTableColumns'
import { ExpenseStatusBadge } from '@/components/expenses/ExpenseStatusBadge'
import { getColumnDisplayValue } from '@/lib/hooks/expenses/UseTableColumns'

interface ExpensesTableProps {
  expenses: Expense[]
  columns: TableColumn[]
  loading: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (columnKey: keyof Expense) => void
  onView?: (expense: Expense) => void
  onEdit?: (expense: Expense) => void
  onDelete?: (expense: Expense) => void
}

interface TableSkeletonProps {
  rows?: number
  columns?: number
}

const TableSkeleton = ({ rows = 10, columns = 6 }: TableSkeletonProps) => (
  <div className="space-y-4">
    {[...Array(rows)].map((_, i) => (
      <div key={i} className="flex space-x-4 py-3 border-b border-border">
        {[...Array(columns)].map((_, j) => (
          <div 
            key={j} 
            className={`h-4 bg-muted rounded animate-pulse ${
              j === 0 ? 'flex-1' : j === columns - 1 ? 'w-24' : 'w-32'
            }`} 
          />
        ))}
      </div>
    ))}
  </div>
)

export const ExpensesTable = ({
  expenses,
  columns,
  loading,
  sortBy,
  sortOrder,
  onSort,
  onView,
  onEdit,
  onDelete
}: ExpensesTableProps) => {
  const getSortIcon = (columnKey: keyof Expense) => {
    if (sortBy !== columnKey) {
      return <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
    }
    return sortOrder === 'asc' 
      ? <ArrowUp className="h-4 w-4 text-foreground" />
      : <ArrowDown className="h-4 w-4 text-foreground" />
  }

  const handleSort = (columnKey: keyof Expense, sortable?: boolean) => {
    if (sortable && onSort) {
      onSort(columnKey)
    }
  }

  const renderCellContent = (expense: Expense, column: TableColumn) => {
    const value = expense[column.key]
    
    if (column.key === 'payment_status') {
      return <ExpenseStatusBadge status={value as any} />
    }
    
    if (column.key === 'total_amount') {
      return (
        <span className="font-medium">
          {getColumnDisplayValue(value, expense, column.key)}
        </span>
      )
    }
    
    if (column.key === 'expense_date') {
      return (
        <span className="text-sm">
          {getColumnDisplayValue(value, expense, column.key)}
        </span>
      )
    }
    
    return getColumnDisplayValue(value, expense, column.key)
  }

  if (loading) {
    return (
      <Card className="p-6">
        <TableSkeleton columns={columns.length + 1} />
      </Card>
    )
  }

  if (expenses.length === 0) {
    return (
      <Card className="p-12 text-center">
        <div className="space-y-4">
          <div className="text-lg font-light text-muted-foreground">No expenses found</div>
          <p className="text-sm text-muted-foreground">
            Try adjusting your search criteria or add a new expense
          </p>
        </div>
      </Card>
    )
  }

  return (
    <>
      {/* Desktop Table */}
      <div className="hidden md:block">
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  {columns.map((column) => (
                    <th 
                      key={column.key}
                      className={`px-4 py-3 text-left text-sm font-medium text-muted-foreground ${
                        column.sortable ? 'cursor-pointer hover:text-foreground transition-colors' : ''
                      }`}
                      onClick={() => handleSort(column.key, column.sortable)}
                    >
                      <div className="flex items-center gap-2">
                        {column.label}
                        {column.sortable && getSortIcon(column.key)}
                      </div>
                    </th>
                  ))}
                  <th className="px-4 py-3 w-12"></th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => (
                  <tr
                    key={expense.id}
                    className="border-b border-border hover:bg-muted/20 transition-colors cursor-pointer"
                    onClick={() => onView?.(expense)}
                  >
                    {columns.map((column) => (
                      <td key={column.key} className="px-4 py-3 text-sm">
                        {renderCellContent(expense, column)}
                      </td>
                    ))}
                    <td className="px-4 py-3">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onView?.(expense)}>
                            <Eye className="h-4 w-4 mr-2" />
                            View
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onEdit?.(expense)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => onDelete?.(expense)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-4">
        {expenses.map((expense) => (
          <Card 
            key={expense.id}
            className="p-4 cursor-pointer hover:bg-muted/20 transition-colors"
            onClick={() => onView?.(expense)}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <h3 className="font-medium text-sm">{expense.description}</h3>
                <p className="text-xs text-muted-foreground">
                  {new Date(expense.expense_date).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">
                  {expense.total_amount} {expense.currency}
                </span>
                <ExpenseStatusBadge status={expense.payment_status} />
              </div>
            </div>
            
            <div className="flex justify-between items-center text-xs text-muted-foreground">
              <span>{getColumnDisplayValue(expense.expense_type, expense, 'expense_type')}</span>
              <span>{getColumnDisplayValue(expense.payment_method, expense, 'payment_method')}</span>
            </div>
          </Card>
        ))}
      </div>
    </>
  )
} 