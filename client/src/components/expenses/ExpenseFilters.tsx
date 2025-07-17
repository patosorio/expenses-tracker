import { Search } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { ExpenseFilters } from "@/lib/types/expenses"
import { PaymentStatus } from "@/lib/types/expenses"
import { UUID } from "crypto"

interface ExpenseFiltersProps {
  filters: ExpenseFilters
  onFiltersChange: (filters: ExpenseFilters) => void
  searchTerm: string
  onSearchChange: (search: string) => void
}

export function ExpenseFilters({
  filters,
  onFiltersChange,
  searchTerm,
  onSearchChange,
}: ExpenseFiltersProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search expenses..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>

          <Select
            value={filters.category_id?.toString() || "all"}
            onValueChange={(value) =>
              onFiltersChange({
                ...filters,
                category_id: value === "all" ? undefined : value as UUID,
              })
            }
          >
            <SelectTrigger className="w-48">
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              {/* Categories will be passed as props later */}
            </SelectContent>
          </Select>

          <Select
            value={filters.payment_status || "all"}
            onValueChange={(value) =>
              onFiltersChange({
                ...filters,
                payment_status: value === "all" ? undefined : value as PaymentStatus,
              })
            }
          >
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value={PaymentStatus.PAID}>Paid</SelectItem>
              <SelectItem value={PaymentStatus.PENDING}>Pending</SelectItem>
              <SelectItem value={PaymentStatus.OVERDUE}>Overdue</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  )
} 