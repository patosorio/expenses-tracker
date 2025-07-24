'use client'

import { useState, useCallback } from 'react'
import { Expense, PaymentStatus, ExpenseType, PaymentMethod } from '@/lib/types/expenses'

export interface TableColumn {
  key: keyof Expense
  label: string
  sortable: boolean
  visible: boolean
  width?: string
}

const DEFAULT_COLUMNS: TableColumn[] = [
  { key: 'description', label: 'Description', sortable: true, visible: true },
  { key: 'expense_date', label: 'Date', sortable: true, visible: true },
  { key: 'expense_type', label: 'Type', sortable: true, visible: true },
  { key: 'base_amount', label: 'Base Amount', sortable: true, visible: false },
  { key: 'tax_amount', label: 'Tax Amount', sortable: true, visible: false },
  { key: 'total_amount', label: 'Total Amount', sortable: true, visible: true },
  { key: 'currency', label: 'Currency', sortable: true, visible: true },
  { key: 'payment_status', label: 'Status', sortable: true, visible: true },
  { key: 'payment_method', label: 'Payment Method', sortable: true, visible: true },
  { key: 'payment_date', label: 'Payment Date', sortable: true, visible: false },
  { key: 'payment_due_date', label: 'Due Date', sortable: true, visible: false },
  { key: 'invoice_number', label: 'Invoice #', sortable: true, visible: false },
  { key: 'category_id', label: 'Category', sortable: true, visible: true },
  { key: 'contact_id', label: 'Contact', sortable: true, visible: false },
  { key: 'notes', label: 'Notes', sortable: false, visible: false },
  { key: 'receipt_url', label: 'Receipt', sortable: false, visible: false },
  { key: 'tags', label: 'Tags', sortable: false, visible: false },
  { key: 'created_at', label: 'Created', sortable: true, visible: false },
  { key: 'updated_at', label: 'Updated', sortable: true, visible: false },
]

export const useTableColumns = () => {
  const [columns, setColumns] = useState<TableColumn[]>(DEFAULT_COLUMNS)

  const toggleColumn = useCallback((columnKey: keyof Expense) => {
    setColumns(prev => 
      prev.map(col => 
        col.key === columnKey 
          ? { ...col, visible: !col.visible }
          : col
      )
    )
  }, [])

  const resetColumns = useCallback(() => {
    setColumns(DEFAULT_COLUMNS)
  }, [])

  const visibleColumns = columns.filter(col => col.visible)

  return {
    columns,
    visibleColumns,
    toggleColumn,
    resetColumns
  }
}

export const getColumnDisplayValue = (value: any, expense: Expense, columnKey: keyof Expense): string => {
  if (value === null || value === undefined) {
    return '-'
  }

  switch (columnKey) {
    case 'expense_date':
    case 'payment_date':
    case 'payment_due_date':
    case 'created_at':
    case 'updated_at':
      return new Date(value).toLocaleDateString()
    
    case 'base_amount':
    case 'tax_amount':
    case 'total_amount':
      return `${value} ${expense.currency}`
    
    case 'payment_status':
      return getPaymentStatusLabel(value as PaymentStatus)
    
    case 'expense_type':
      return getExpenseTypeLabel(value as ExpenseType)
    
    case 'payment_method':
      return getPaymentMethodLabel(value as PaymentMethod)
    
    case 'category_id':
    case 'contact_id':
    case 'tax_config_id':
      // TODO: Get names from context or API
      return value.toString()
    
    case 'notes':
      return value.length > 50 ? `${value.substring(0, 50)}...` : value
    
    case 'receipt_url':
      return value ? '📄 Receipt' : '-'
    
    case 'invoice_number':
      return value || '-'
    
    case 'tags':
      return Array.isArray(value) && value.length > 0 ? value.join(', ') : '-'
    
    default:
      return String(value)
  }
}

const getPaymentStatusLabel = (status: PaymentStatus): string => {
  switch (status) {
    case PaymentStatus.PAID:
      return 'Paid'
    case PaymentStatus.PENDING:
      return 'Pending'
    case PaymentStatus.REFUNDED:
      return 'Refunded'
    default:
      return status
  }
}

const getExpenseTypeLabel = (type: ExpenseType): string => {
  switch (type) {
    case ExpenseType.SIMPLE:
      return 'Receipt'
    case ExpenseType.INVOICE:
      return 'Invoice'
    default:
      return type
  }
}

const getPaymentMethodLabel = (method: PaymentMethod): string => {
  switch (method) {
    case PaymentMethod.CASH:
      return 'Cash'
    case PaymentMethod.CARD:
      return 'Card'
    case PaymentMethod.BANK_TRANSFER:
      return 'Bank Transfer'
    case PaymentMethod.DIGITAL_WALLET:
      return 'Digital Wallet'
    default:
      return method
  }
} 