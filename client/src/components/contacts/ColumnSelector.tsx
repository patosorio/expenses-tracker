'use client'

import { Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuItem
} from '@/components/ui/dropdown-menu'
import { Contact, TableColumn } from '@/lib/types/contacts'

interface ColumnSelectorProps {
  columns: TableColumn[]
  onToggle: (columnKey: keyof Contact) => void
  onReset: () => void
}

export const ColumnSelector = ({ columns, onToggle, onReset }: ColumnSelectorProps) => {
  const visibleCount = columns.filter(col => !col.hidden).length
  const totalCount = columns.length

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <Settings className="h-4 w-4 mr-2" />
          Columns ({visibleCount}/{totalCount})
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <div className="px-2 py-1.5 text-sm font-medium text-muted-foreground">
          Show/Hide Columns
        </div>
        <DropdownMenuSeparator />
        
        {columns.map((column) => (
          <DropdownMenuCheckboxItem
            key={column.key}
            checked={!column.hidden}
            onCheckedChange={() => onToggle(column.key)}
            className="text-sm"
          >
            {column.label}
          </DropdownMenuCheckboxItem>
        ))}
        
        <DropdownMenuSeparator />
        <DropdownMenuItem 
          onClick={onReset}
          className="text-sm text-muted-foreground"
        >
          Reset to default
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 