'use client'

import React from 'react'
import { Search, Filter, X, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Expense, ExpenseFilters, ExpenseType, PaymentStatus, PaymentMethod } from '@/types/expenses'
import { TableColumn } from '@/hooks/expenses/UseTableColumns'

interface ExpensesToolbarProps {
  filters: ExpenseFilters
  onFiltersChange: (filters: ExpenseFilters) => void
  onClearFilters: () => void
  columns: TableColumn[]
  onColumnToggle: (columnKey: keyof Expense) => void
  onColumnReset: () => void
  totalExpenses: number
  hasActiveFilters: boolean
}

export const ExpensesToolbar = ({
  filters,
  onFiltersChange,
  onClearFilters,
  columns,
  onColumnToggle,
  onColumnReset,
  totalExpenses,
  hasActiveFilters
}: ExpensesToolbarProps) => {
  const handleSearchChange = (value: string) => {
    onFiltersChange({ ...filters, search: value })
  }

  const handleFilterChange = (key: keyof ExpenseFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const handleClearFilters = () => {
    onClearFilters()
  }

  const hiddenColumns = columns.filter(col => !col.visible)

  return (
    <Card className="p-4">
      <div className="flex flex-col gap-4">
        {/* Search and Quick Actions */}
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search expenses..."
              value={filters.search || ''}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Columns
                {hiddenColumns.length > 0 && (
                  <span className="ml-2 bg-primary text-primary-foreground text-xs rounded-full px-2 py-0.5">
                    {hiddenColumns.length}
                  </span>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <div className="px-2 py-1.5 text-sm font-medium">Toggle Columns</div>
              <DropdownMenuSeparator />
              {columns.map((column) => (
                <DropdownMenuItem
                  key={column.key}
                  onClick={() => onColumnToggle(column.key)}
                  className="flex items-center justify-between"
                >
                  <span>{column.label}</span>
                  {column.visible && (
                    <div className="w-2 h-2 bg-primary rounded-full" />
                  )}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onColumnReset}>
                Reset to Default
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {hasActiveFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearFilters}
              className="text-muted-foreground"
            >
              <X className="h-4 w-4 mr-2" />
              Clear Filters
            </Button>
          )}
        </div>

        {/* Advanced Filters */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Type:</span>
            <Select
              value={filters.expense_type || 'all'}
              onValueChange={(value) => handleFilterChange('expense_type', value === 'all' ? undefined : value)}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                <SelectItem value={ExpenseType.SIMPLE}>Receipt</SelectItem>
                <SelectItem value={ExpenseType.INVOICE}>Invoice</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Status:</span>
            <Select
              value={filters.payment_status || 'all'}
              onValueChange={(value) => handleFilterChange('payment_status', value === 'all' ? undefined : value)}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="All status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All status</SelectItem>
                <SelectItem value={PaymentStatus.PAID}>Paid</SelectItem>
                <SelectItem value={PaymentStatus.PENDING}>Pending</SelectItem>
                <SelectItem value={PaymentStatus.REFUNDED}>Refunded</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Payment:</span>
            <Select
              value={filters.payment_method || 'all'}
              onValueChange={(value) => handleFilterChange('payment_method', value === 'all' ? undefined : value)}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All methods" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All methods</SelectItem>
                <SelectItem value={PaymentMethod.CASH}>Cash</SelectItem>
                <SelectItem value={PaymentMethod.CARD}>Card</SelectItem>
                <SelectItem value={PaymentMethod.BANK_TRANSFER}>Bank Transfer</SelectItem>
                <SelectItem value={PaymentMethod.DIGITAL_WALLET}>Digital Wallet</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Amount:</span>
            <Input
              type="number"
              placeholder="Min"
              value={filters.min_amount || ''}
              onChange={(e) => handleFilterChange('min_amount', e.target.value ? Number(e.target.value) : undefined)}
              className="w-20"
            />
            <span className="text-sm text-muted-foreground">-</span>
            <Input
              type="number"
              placeholder="Max"
              value={filters.max_amount || ''}
              onChange={(e) => handleFilterChange('max_amount', e.target.value ? Number(e.target.value) : undefined)}
              className="w-20"
            />
          </div>
        </div>

        {/* Results Summary */}
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {totalExpenses} expense{totalExpenses !== 1 ? 's' : ''} found
            {hasActiveFilters && ' with current filters'}
          </span>
        </div>
      </div>
    </Card>
  )
} 