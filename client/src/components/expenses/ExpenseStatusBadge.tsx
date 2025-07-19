import { Badge } from '@/components/ui/badge'
import { PaymentStatus } from '@/types/expenses'

interface ExpenseStatusBadgeProps {
  status: PaymentStatus
}

export const ExpenseStatusBadge = ({ status }: ExpenseStatusBadgeProps) => {
  const getStatusConfig = (status: PaymentStatus) => {
    switch (status) {
      case PaymentStatus.PAID:
        return {
          label: 'Paid',
          variant: 'default' as const,
          className: 'bg-green-100 text-green-800 border-green-200'
        }
      case PaymentStatus.PENDING:
        return {
          label: 'Pending',
          variant: 'secondary' as const,
          className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
        }
      case PaymentStatus.REFUNDED:
        return {
          label: 'Refunded',
          variant: 'outline' as const,
          className: 'bg-blue-100 text-blue-800 border-blue-200'
        }
      default:
        return {
          label: status,
          variant: 'outline' as const,
          className: 'bg-gray-100 text-gray-800 border-gray-200'
        }
    }
  }

  const config = getStatusConfig(status)

  return (
    <Badge 
      variant={config.variant}
      className={`text-xs font-medium ${config.className}`}
    >
      {config.label}
    </Badge>
  )
} 