import { 
  Contact, 
  ContactFilters, 
  ContactListResponse, 
  CreateContactPayload,
  UpdateContactPayload,
  ContactSummaryResponse,
  ContactType
} from "@/lib/types/contacts"
import { apiClient } from "./client"

export class ContactsApi {
  /**
   * Get paginated list of contacts with filters
   */
  async getContacts(
    page: number = 1,
    limit: number = 25,
    filters?: ContactFilters,
    _sortBy?: string,
    _sortOrder?: "asc" | "desc"
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

    const response = await apiClient.get<ContactListResponse>(`/contacts/?${searchParams}`)
    return response.data
  }

  /**
   * Search for vendors and suppliers by name
   */
  async searchVendorsAndSuppliers(
    searchTerm: string,
    limit: number = 10
  ): Promise<Contact[]> {
    if (searchTerm.length < 2) {
      return []
    }

    try {
      // Make two separate calls to get both VENDOR and SUPPLIER contacts using autocomplete endpoint
      const [vendorsResponse, suppliersResponse] = await Promise.all([
        apiClient.get<Contact[]>(`/contacts/search/autocomplete?q=${searchTerm}&limit=${limit}&contact_type=VENDOR`),
        apiClient.get<Contact[]>(`/contacts/search/autocomplete?q=${searchTerm}&limit=${limit}&contact_type=SUPPLIER`)
      ])

      // Combine and sort results
      const allContacts = [
        ...vendorsResponse.data,
        ...suppliersResponse.data
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

  /**
   * Get a single contact by ID
   */
  async getContactById(id: string): Promise<Contact> {
    const response = await apiClient.get<Contact>(`/contacts/${id}/`)
    return response.data
  }

  /**
   * Create a new contact
   */
  async createContact(data: CreateContactPayload): Promise<Contact> {
    const response = await apiClient.post<Contact>('/contacts/', {
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
    return response.data
  }

  /**
   * Update an existing contact
   */
  async updateContact(id: string, data: UpdateContactPayload): Promise<Contact> {
    const response = await apiClient.put<Contact>(`/contacts/${id}/`, data)
    return response.data
  }

  /**
   * Delete a contact
   */
  async deleteContact(id: string): Promise<void> {
    await apiClient.delete<void>(`/contacts/${id}/`)
  }

  /**
   * Get contacts summary statistics
   */
  async getContactsSummary(): Promise<ContactSummaryResponse> {
    const response = await apiClient.get<ContactSummaryResponse>('/contacts/summary/')
    return response.data
  }
}

// Export a singleton instance
export const contactsApi = new ContactsApi(); 