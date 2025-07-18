import { 
  Contact, 
  ContactFilters, 
  ContactListResponse, 
  CreateContactPayload,
  UpdateContactPayload,
  ContactSummaryResponse,
  ContactType
} from "@/lib/types/contacts"
import { UUID } from "crypto"
import { getAuth } from "firebase/auth"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const API_BASE = `${API_URL}/api/v1`

async function getAuthHeaders() {
  // Try to get token from localStorage first
  const storedToken = localStorage.getItem('firebase-token')
  
  if (storedToken) {
    return {
      "Authorization": `Bearer ${storedToken}`,
      "Content-Type": "application/json",
    }
  }
  
  // Fallback to getting token from Firebase auth
  const auth = getAuth()
  const user = auth.currentUser
  
  if (!user) {
    console.warn('No authenticated user found')
    throw new Error('User not authenticated')
  }
  
  const token = await user.getIdToken()
  
  return {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  }
}

export async function getContacts(
  page: number = 1,
  limit: number = 25,
  filters?: ContactFilters,
  sortBy?: string,
  sortOrder?: "asc" | "desc"
): Promise<ContactListResponse> {
  const searchParams = new URLSearchParams({
    page: page.toString(),
    per_page: limit.toString(),
    ...(filters?.contact_type && { contact_type: filters.contact_type }),
    ...(filters?.country && { country: filters.country }),
    ...(filters?.is_active !== undefined && { is_active: filters.is_active.toString() }),
    ...(filters?.search && { search: filters.search }),
    ...(filters?.tags && filters.tags.length > 0 && { tags: filters.tags.join(',') })
  })

  const url = `${API_BASE}/contacts/?${searchParams}`
  
  try {
    const headers = await getAuthHeaders()
    
    const response = await fetch(url, {
      headers,
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Response error text:', errorText)
      throw new Error(`Failed to fetch contacts: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error in getContacts:', error)
    throw error
  }
}

export async function searchVendorsAndSuppliers(
  searchTerm: string,
  limit: number = 10
): Promise<Contact[]> {
  if (searchTerm.length < 2) {
    return []
  }

  try {
    // Make two separate calls to get both VENDOR and SUPPLIER contacts
    const [vendorsResponse, suppliersResponse] = await Promise.all([
      getContacts(1, limit, { 
        search: searchTerm, 
        contact_type: ContactType.VENDOR 
      }),
      getContacts(1, limit, { 
        search: searchTerm, 
        contact_type: ContactType.SUPPLIER 
      })
    ])

    // Combine and sort results
    const allContacts = [
      ...vendorsResponse.contacts,
      ...suppliersResponse.contacts
    ]

    // Sort by name and limit to requested number
    return allContacts
      .sort((a, b) => a.name.localeCompare(b.name))
      .slice(0, limit)
  } catch (error) {
    console.error('Error in searchVendorsAndSuppliers:', error)
    throw error
  }
}

export async function getContactById(id: UUID): Promise<Contact> {
  const response = await fetch(`${API_BASE}/contacts/${id}/`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch contact")
  }

  return response.json()
}

export async function createContact(data: CreateContactPayload): Promise<Contact> {
  try {
    console.log('Creating contact with data:', data)
    const response = await fetch(`${API_BASE}/contacts/`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify({
        name: data.name,
        contact_type: data.contact_type,
        email: data.email,
        phone: data.phone,
        address_line1: data.address_line1,
        address_line2: data.address_line2,
        city: data.city,
        state_province: data.state_province,
        postal_code: data.postal_code,
        country: data.country || 'PT',
        tax_number: data.tax_number,
        website: data.website,
        notes: data.notes,
        tags: data.tags || [],
        custom_fields: data.custom_fields || {}
      })
    })

    if (!response.ok) {
      const errorData = await response.json()
      console.error('Backend error response:', errorData)
      
      let errorMessage = "Failed to create contact"
      if (errorData.detail) {
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (typeof errorData.detail === 'object') {
          errorMessage = JSON.stringify(errorData.detail)
        }
      }
      
      throw new Error(errorMessage)
    }

    return response.json()
  } catch (error) {
    console.error('Error creating contact:', error)
    throw error
  }
}

export async function updateContact(id: UUID, data: UpdateContactPayload): Promise<Contact> {
  try {
    console.log('Updating contact with data:', data)
    const response = await fetch(`${API_BASE}/contacts/${id}/`, {
      method: "PUT",
      headers: await getAuthHeaders(),
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || "Failed to update contact")
    }

    return response.json()
  } catch (error) {
    console.error('Error updating contact:', error)
    throw error
  }
}

export async function deleteContact(id: UUID): Promise<void> {
  try {
    console.log('Deleting contact:', id)
    const response = await fetch(`${API_BASE}/contacts/${id}/`, {
      method: "DELETE",
      headers: await getAuthHeaders(),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || "Failed to delete contact")
    }
  } catch (error) {
    console.error('Error deleting contact:', error)
    throw error
  }
}

export async function getContactsSummary(): Promise<ContactSummaryResponse> {
  const response = await fetch(`${API_BASE}/contacts/summary/`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error("Failed to fetch contacts summary")
  }

  return response.json()
} 