'use client'

import { Expense } from '@/lib/types/expenses'
import { ExpenseDetailHeader } from './ExpenseDetailHeader'
import { ExpenseAmountSection } from './ExpenseAmountSection'
import { ExpenseBasicInfoSection } from './ExpenseBasicInfoSection'
import { ExpenseStatusSection } from './ExpenseStatusSection'
import { ExpenseTagsSection } from './ExpenseTagsSection'
import { ExpenseDocumentsSection } from './ExpenseDocumentsSection'
import { ExpenseCustomFieldsSection } from './ExpenseCustomFieldsSection'

interface ExpenseDetailViewProps {
  expense: Expense
}

export function ExpenseDetailView({ expense }: ExpenseDetailViewProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <ExpenseDetailHeader expense={expense} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Financial Details */}
          <ExpenseAmountSection expense={expense} />
          
          {/* Basic Information */}
          <ExpenseBasicInfoSection expense={expense} />
          
          {/* Custom Fields */}
          <ExpenseCustomFieldsSection expense={expense} />
        </div>

        {/* Sidebar - 1 column */}
        <div className="space-y-6">
          {/* Status */}
          <ExpenseStatusSection expense={expense} />
          
          {/* Tags */}
          <ExpenseTagsSection expense={expense} />
          
          {/* Documents */}
          <ExpenseDocumentsSection expense={expense} />
        </div>
      </div>
    </div>
  )
} 