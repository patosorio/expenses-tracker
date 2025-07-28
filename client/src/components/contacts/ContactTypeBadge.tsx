'use client'

import { ContactType } from '@/lib/types/contacts'
import { getContactTypeBadgeVariant } from '@/lib/hooks/contacts/UseTableColumns'

interface ContactTypeBadgeProps {
  type: ContactType
  className?: string
}

export const ContactTypeBadge = ({ type, className = '' }: ContactTypeBadgeProps) => {
  const variant = getContactTypeBadgeVariant(type)
  
  return (
    <span 
      className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${variant} ${className}`}
    >
      {type}
    </span>
  )
} 