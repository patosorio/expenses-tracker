import { UUID } from "crypto"

export enum ContactType {
  CLIENT = "CLIENT",
  VENDOR = "VENDOR", 
  SUPPLIER = "SUPPLIER"
}

export interface Contact {
  id: string
  name: string
  contact_type: ContactType
  email?: string
  phone?: string
  address_line1?: string
  address_line2?: string
  city?: string
  state_province?: string
  postal_code?: string
  country: string
  tax_number?: string
  website?: string
  notes?: string
  tags?: string[]
  custom_fields?: Record<string, any>
  user_id: string
  created_at: string
  updated_at?: string
  is_active: boolean
  full_address: string
}

export interface ContactFilters {
  search?: string
  contact_type?: ContactType
  country?: string
  is_active?: boolean
  tags?: string[]
}

export interface ContactListResponse {
  contacts: Contact[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface CreateContactPayload {
  name: string
  contact_type: ContactType
  email?: string
  phone?: string
  address_line1?: string
  address_line2?: string
  city?: string
  state_province?: string
  postal_code?: string
  country?: string
  tax_number?: string
  website?: string
  notes?: string
  tags?: string[]
  custom_fields?: Record<string, any>
}

export interface UpdateContactPayload extends Partial<CreateContactPayload> {
  is_active?: boolean
}

export interface ContactSummary {
  id: UUID
  name: string
  contact_type: ContactType
  email?: string
}

export interface ContactSummaryResponse {
  contacts: ContactSummary[]
}

export interface TableColumn {
  key: keyof Contact
  label: string
  sortable?: boolean
  hidden?: boolean
  render?: (value: any, contact: Contact) => React.ReactNode
} 