'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Receipt, FileText, Upload, Eye } from 'lucide-react'
import { Expense } from '@/lib/types/expenses'

interface ExpenseDocumentsSectionProps {
  expense: Expense
}

export function ExpenseDocumentsSection({ expense }: ExpenseDocumentsSectionProps) {
  const hasReceipt = expense.receipt_url
  const hasAttachments = false // TODO: Implement when attachments are available

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-light">Documents</CardTitle>
        <CardDescription>Receipts and supporting documents</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Receipt */}
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Receipt</h3>
          {hasReceipt ? (
            <div className="flex items-center gap-2">
              <Receipt className="h-4 w-4 text-muted-foreground" />
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(expense.receipt_url, '_blank')}
                className="gap-2"
              >
                <Eye className="h-3 w-3" />
                View Receipt
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Receipt className="h-4 w-4" />
              <span className="text-sm">No receipt attached</span>
            </div>
          )}
        </div>

        {/* Attachments */}
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Attachments</h3>
          {hasAttachments ? (
            <div className="space-y-2">
              {/* TODO: Render attachments when available */}
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">No attachments yet</span>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-muted-foreground">
              <FileText className="h-4 w-4" />
              <span className="text-sm">No attachments</span>
            </div>
          )}
        </div>

        {/* Upload Button */}
        <div className="pt-2">
          <Button variant="outline" size="sm" className="gap-2">
            <Upload className="h-3 w-3" />
            Upload Document
          </Button>
        </div>
      </CardContent>
    </Card>
  )
} 