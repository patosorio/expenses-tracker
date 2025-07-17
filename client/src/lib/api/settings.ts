import {
  UserSettings,
  UserSettingsUpdate,
  BusinessSettings,
  BusinessSettingsUpdate,
  TaxConfiguration,
  TaxConfigurationCreate,
  TaxConfigurationUpdate,
  TeamMember,
  TeamInvitation,
  Category,
  CategoryFormData,
  CategoryWithChildren,
  SettingsResponse,
  IntegrationSettings,
  ApiKeyConfiguration,
  ExportConfiguration,
} from '@/lib/types/settings'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

// Helper function for API calls
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Get token from AuthContext
  const token = localStorage.getItem('firebase-token')
  
  if (!token) {
    throw new Error('Not authenticated')
  }
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ 
      detail: `HTTP ${response.status}: ${response.statusText}` 
    }))
    throw new Error(error.detail || `Request failed with status ${response.status}`)
  }

  return response.json()
}

// User Settings API
export const userSettingsApi = {
  /**
   * Get current user settings
   */
  getUserSettings: (): Promise<UserSettings> =>
    apiCall<UserSettings>('/settings/user'),

  /**
   * Update user settings
   */
  updateUserSettings: (settings: UserSettingsUpdate): Promise<UserSettings> =>
    apiCall<UserSettings>('/settings/user', {
      method: 'PATCH',
      body: JSON.stringify(settings),
    }),

  /**
   * Reset user settings to defaults
   */
  resetUserSettings: (): Promise<UserSettings> =>
    apiCall<UserSettings>('/settings/user/reset', {
      method: 'POST',
    }),
}

// Business Settings API
export const businessSettingsApi = {
  /**
   * Get business settings
   */
  getBusinessSettings: (): Promise<BusinessSettings> =>
    apiCall<BusinessSettings>('/settings/business'),

  /**
   * Update business settings
   */
  updateBusinessSettings: (settings: BusinessSettingsUpdate): Promise<BusinessSettings> =>
    apiCall<BusinessSettings>('/settings/business', {
      method: 'PATCH',
      body: JSON.stringify(settings),
    }),
}

// Tax Configuration API
export const taxConfigApi = {
  /**
   * Get all tax configurations
   */
  getTaxConfigurations: (): Promise<TaxConfiguration[]> =>
    apiCall<TaxConfiguration[]>('/settings/tax-configurations'),

  /**
   * Create new tax configuration
   */
  createTaxConfiguration: (config: TaxConfigurationCreate): Promise<TaxConfiguration> =>
    apiCall<TaxConfiguration>('/settings/tax-configurations', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  /**
   * Update tax configuration
   */
  updateTaxConfiguration: (id: string, config: TaxConfigurationUpdate): Promise<TaxConfiguration> =>
    apiCall<TaxConfiguration>(`/settings/tax-configurations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(config),
    }),

  /**
   * Delete tax configuration
   */
  deleteTaxConfiguration: (id: string): Promise<void> =>
    apiCall<void>(`/settings/tax-configurations/${id}`, {
      method: 'DELETE',
    }),

  /**
   * Set default tax configuration
   */
  setDefaultTaxConfiguration: (id: string): Promise<TaxConfiguration> =>
    apiCall<TaxConfiguration>(`/settings/tax-configurations/${id}/default`, {
      method: 'POST',
    }),
}

// Team Management API
export const teamApi = {
  /**
   * Get all team members
   */
  getTeamMembers: (): Promise<TeamMember[]> =>
    apiCall<TeamMember[]>('/settings/team/members'),

  /**
   * Invite team member
   */
  inviteTeamMember: (invitation: TeamInvitation): Promise<TeamMember> =>
    apiCall<TeamMember>('/settings/team/invite', {
      method: 'POST',
      body: JSON.stringify(invitation),
    }),

  /**
   * Update team member
   */
  updateTeamMember: (id: string, updates: Partial<TeamMember>): Promise<TeamMember> =>
    apiCall<TeamMember>(`/settings/team/members/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),

  /**
   * Remove team member
   */
  removeTeamMember: (id: string): Promise<void> =>
    apiCall<void>(`/settings/team/members/${id}`, {
      method: 'DELETE',
    }),

  /**
   * Resend invitation
   */
  resendInvitation: (id: string): Promise<TeamMember> =>
    apiCall<TeamMember>(`/settings/team/members/${id}/resend`, {
      method: 'POST',
    }),

  /**
   * Cancel invitation
   */
  cancelInvitation: (id: string): Promise<void> =>
    apiCall<void>(`/settings/team/members/${id}/cancel`, {
      method: 'POST',
    }),
}

// Categories API
export const categoriesApi = {
  /**
   * Get all categories
   */
  getCategories: (): Promise<Category[]> =>
    apiCall<{ categories: Category[] }>('/categories').then(response => response.categories),

  /**
   * Get categories with hierarchy
   */
  getCategoriesHierarchy: (): Promise<CategoryWithChildren[]> =>
    apiCall<{ categories: Category[] }>('/categories').then(response => {
      // Build hierarchy
      const categories = response.categories
      const categoryMap = new Map(
        categories.map(cat => [
          cat.id, 
          { ...cat, children: [] } as CategoryWithChildren
        ])
      )
      const rootCategories: CategoryWithChildren[] = []

      // Build parent-child relationships
      categories.forEach(category => {
        const categoryWithChildren = categoryMap.get(category.id)!
        if (category.parentId) {
          const parent = categoryMap.get(category.parentId)
          if (parent) {
            parent.children.push(categoryWithChildren)
          }
        } else {
          rootCategories.push(categoryWithChildren)
        }
      })

      return rootCategories
    }),

  /**
   * Create new category
   */
  createCategory: (category: CategoryFormData): Promise<Category> =>
    apiCall<Category>('/categories', {
      method: 'POST',
      body: JSON.stringify({
        name: category.name,
        type: category.type,
        color: category.color,
        icon: category.icon,
        parent_id: category.parentId, 
        is_default: category.isDefault
      }),
    }),

  /**
   * Update category
   */
  updateCategory: (id: string, category: Partial<CategoryFormData>): Promise<Category> =>
    apiCall<Category>(`/categories/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(category),
    }),

  /**
   * Delete category
   */
  deleteCategory: (id: string): Promise<void> =>
    apiCall<void>(`/categories/${id}`, {
      method: 'DELETE',
    }),

  /**
   * Move category to different parent
   */
  moveCategory: (id: string, parentId: string | null): Promise<Category> =>
    apiCall<Category>(`/categories/${id}/move`, {
      method: 'POST',
      body: JSON.stringify({ parentId }),
    }),
}

// Integration Settings API
export const integrationApi = {
  /**
   * Get integration settings
   */
  getIntegrationSettings: (): Promise<IntegrationSettings> =>
    apiCall<IntegrationSettings>('/settings/integrations'),

  /**
   * Create API key
   */
  createApiKey: (name: string, service: string): Promise<ApiKeyConfiguration> =>
    apiCall<ApiKeyConfiguration>('/settings/integrations/api-keys', {
      method: 'POST',
      body: JSON.stringify({ name, service }),
    }),

  /**
   * Delete API key
   */
  deleteApiKey: (id: string): Promise<void> =>
    apiCall<void>(`/settings/integrations/api-keys/${id}`, {
      method: 'DELETE',
    }),

  /**
   * Update export settings
   */
  updateExportSettings: (settings: Partial<ExportConfiguration>): Promise<ExportConfiguration> =>
    apiCall<ExportConfiguration>('/settings/integrations/export', {
      method: 'PATCH',
      body: JSON.stringify(settings),
    }),

  /**
   * Test webhook
   */
  testWebhook: (url: string): Promise<{ success: boolean; responseTime: number }> =>
    apiCall('/settings/integrations/webhooks/test', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),
}

// Data Export API
export const dataExportApi = {
  /**
   * Export data in specified format
   */
  exportData: (format: 'csv' | 'pdf' | 'json', dateRange?: { from: string; to: string }): Promise<{ downloadUrl: string }> =>
    apiCall('/settings/export/data', {
      method: 'POST',
      body: JSON.stringify({ format, dateRange }),
    }),

  /**
   * Get export history
   */
  getExportHistory: (): Promise<Array<{ id: string; format: string; createdAt: string; downloadUrl: string; status: string }>> =>
    apiCall('/settings/export/history'),

  /**
   * Schedule recurring export
   */
  scheduleExport: (schedule: { frequency: string; format: string; recipients: string[] }): Promise<void> =>
    apiCall('/settings/export/schedule', {
      method: 'POST',
      body: JSON.stringify(schedule),
    }),
}

// Preferences API (timezone, language, etc.)
export const preferencesApi = {
  /**
   * Get available timezones
   */
  getTimezones: (): Promise<Array<{ value: string; label: string; offset: string; region: string }>> =>
    apiCall('/settings/preferences/timezones'),

  /**
   * Get available languages
   */
  getLanguages: (): Promise<Array<{ code: string; name: string; nativeName: string; flag: string }>> =>
    apiCall('/settings/preferences/languages'),

  /**
   * Get available currencies
   */
  getCurrencies: (): Promise<Array<{ code: string; name: string; symbol: string; flag: string }>> =>
    apiCall('/settings/preferences/currencies'),
}

// Consolidated settings API object
export const settingsApi = {
  user: userSettingsApi,
  business: businessSettingsApi,
  taxConfig: taxConfigApi,
  team: teamApi,
  categories: categoriesApi,
  integration: integrationApi,
  dataExport: dataExportApi,
  preferences: preferencesApi,
}
