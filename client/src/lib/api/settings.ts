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
  IntegrationSettings,
  ApiKeyConfiguration,
  ExportConfiguration,
} from '@/lib/types/settings'
import { apiClient } from './client'

export class UserSettingsApi {
  /**
   * Get current user settings
   */
  async getUserSettings(): Promise<UserSettings> {
    const response = await apiClient.get<UserSettings>('/settings/user')
    return response.data
  }

  /**
   * Update user settings
   */
  async updateUserSettings(settings: UserSettingsUpdate): Promise<UserSettings> {
    const response = await apiClient.patch<UserSettings>('/settings/user', settings)
    return response.data
  }

  /**
   * Reset user settings to defaults
   */
  async resetUserSettings(): Promise<UserSettings> {
    const response = await apiClient.post<UserSettings>('/settings/user/reset')
    return response.data
  }
}

export class BusinessSettingsApi {
  /**
   * Get business settings
   */
  async getBusinessSettings(): Promise<BusinessSettings> {
    const response = await apiClient.get<BusinessSettings>('/settings/business')
    return response.data
  }

  /**
   * Update business settings
   */
  async updateBusinessSettings(settings: BusinessSettingsUpdate): Promise<BusinessSettings> {
    const response = await apiClient.patch<BusinessSettings>('/settings/business', settings)
    return response.data
  }
}

export class TaxConfigApi {
  /**
   * Get all tax configurations
   */
  async getTaxConfigurations(): Promise<TaxConfiguration[]> {
    const response = await apiClient.get<TaxConfiguration[]>('/settings/tax-configurations')
    return response.data
  }

  /**
   * Create new tax configuration
   */
  async createTaxConfiguration(config: TaxConfigurationCreate): Promise<TaxConfiguration> {
    const response = await apiClient.post<TaxConfiguration>('/settings/tax-configurations', config)
    return response.data
  }

  /**
   * Update tax configuration
   */
  async updateTaxConfiguration(id: string, config: TaxConfigurationUpdate): Promise<TaxConfiguration> {
    const response = await apiClient.patch<TaxConfiguration>(`/settings/tax-configurations/${id}`, config)
    return response.data
  }

  /**
   * Delete tax configuration
   */
  async deleteTaxConfiguration(id: string): Promise<void> {
    await apiClient.delete<void>(`/settings/tax-configurations/${id}`)
  }

  /**
   * Set default tax configuration
   */
  async setDefaultTaxConfiguration(id: string): Promise<TaxConfiguration> {
    const response = await apiClient.post<TaxConfiguration>(`/settings/tax-configurations/${id}/default`)
    return response.data
  }
}

export class TeamApi {
  /**
   * Get all team members
   */
  async getTeamMembers(): Promise<TeamMember[]> {
    const response = await apiClient.get<TeamMember[]>('/settings/team/members')
    return response.data
  }

  /**
   * Invite team member
   */
  async inviteTeamMember(invitation: TeamInvitation): Promise<TeamMember> {
    const response = await apiClient.post<TeamMember>('/settings/team/invite', invitation)
    return response.data
  }

  /**
   * Update team member
   */
  async updateTeamMember(id: string, updates: Partial<TeamMember>): Promise<TeamMember> {
    const response = await apiClient.patch<TeamMember>(`/settings/team/members/${id}`, updates)
    return response.data
  }

  /**
   * Remove team member
   */
  async removeTeamMember(id: string): Promise<void> {
    await apiClient.delete<void>(`/settings/team/members/${id}`)
  }

  /**
   * Resend invitation
   */
  async resendInvitation(id: string): Promise<TeamMember> {
    const response = await apiClient.post<TeamMember>(`/settings/team/members/${id}/resend`)
    return response.data
  }

  /**
   * Cancel invitation
   */
  async cancelInvitation(id: string): Promise<void> {
    await apiClient.post<void>(`/settings/team/members/${id}/cancel`)
  }
}

export class CategoriesApi {
  /**
   * Get all categories
   */
  async getCategories(): Promise<Category[]> {
    const response = await apiClient.get<{ categories: Category[] }>('/categories')
    return response.data.categories
  }

  /**
   * Get categories with hierarchy
   */
  async getCategoriesHierarchy(): Promise<CategoryWithChildren[]> {
    const response = await apiClient.get<{ categories: Category[] }>('/categories')
    // Build hierarchy
    const categories = response.data.categories
    const categoryMap = new Map(
      categories.map((cat: Category) => [
        cat.id, 
        { ...cat, children: [] } as CategoryWithChildren
      ])
    )
    const rootCategories: CategoryWithChildren[] = []

    // Build parent-child relationships
    categories.forEach((category: Category) => {
      const categoryWithChildren = categoryMap.get(category.id)!
      if (category.parent_id) {
        const parent = categoryMap.get(category.parent_id)
        if (parent) {
          parent.children.push(categoryWithChildren)
        }
      } else {
        rootCategories.push(categoryWithChildren)
      }
    })

    return rootCategories
  }

  /**
   * Create new category
   */
  async createCategory(category: CategoryFormData): Promise<Category> {
    const response = await apiClient.post<Category>('/categories', {
      name: category.name,
      type: category.type,
      color: category.color,
      icon: category.icon,
      parent_id: category.parent_id, 
      is_default: category.is_default
    })
    return response.data
  }

  /**
   * Update category
   */
  async updateCategory(id: string, category: Partial<CategoryFormData>): Promise<Category> {
    const response = await apiClient.patch<Category>(`/categories/${id}`, category)
    return response.data
  }

  /**
   * Delete category
   */
  async deleteCategory(id: string): Promise<void> {
    await apiClient.delete<void>(`/categories/${id}`)
  }

  /**
   * Move category to different parent
   */
  async moveCategory(id: string, parentId: string | null): Promise<Category> {
    const response = await apiClient.post<Category>(`/categories/${id}/move`, { parentId })
    return response.data
  }
}

export class IntegrationApi {
  /**
   * Get integration settings
   */
  async getIntegrationSettings(): Promise<IntegrationSettings> {
    const response = await apiClient.get<IntegrationSettings>('/settings/integrations')
    return response.data
  }

  /**
   * Create API key
   */
  async createApiKey(name: string, service: string): Promise<ApiKeyConfiguration> {
    const response = await apiClient.post<ApiKeyConfiguration>('/settings/integrations/api-keys', { name, service })
    return response.data
  }

  /**
   * Delete API key
   */
  async deleteApiKey(id: string): Promise<void> {
    await apiClient.delete<void>(`/settings/integrations/api-keys/${id}`)
  }

  /**
   * Update export settings
   */
  async updateExportSettings(settings: Partial<ExportConfiguration>): Promise<ExportConfiguration> {
    const response = await apiClient.patch<ExportConfiguration>('/settings/integrations/export', settings)
    return response.data
  }

  /**
   * Test webhook
   */
  async testWebhook(url: string): Promise<{ success: boolean; responseTime: number }> {
    const response = await apiClient.post<{ success: boolean; responseTime: number }>('/settings/integrations/webhooks/test', { url })
    return response.data
  }
}

export class DataExportApi {
  /**
   * Export data in specified format
   */
  async exportData(format: 'csv' | 'pdf' | 'json', dateRange?: { from: string; to: string }): Promise<{ downloadUrl: string }> {
    const response = await apiClient.post<{ downloadUrl: string }>('/settings/export/data', { format, dateRange })
    return response.data
  }

  /**
   * Get export history
   */
  async getExportHistory(): Promise<Array<{ id: string; format: string; createdAt: string; downloadUrl: string; status: string }>> {
    const response = await apiClient.get<Array<{ id: string; format: string; createdAt: string; downloadUrl: string; status: string }>>('/settings/export/history')
    return response.data
  }

  /**
   * Schedule recurring export
   */
  async scheduleExport(schedule: { frequency: string; format: string; recipients: string[] }): Promise<void> {
    await apiClient.post<void>('/settings/export/schedule', schedule)
  }
}

export class PreferencesApi {
  /**
   * Get available timezones
   */
  async getTimezones(): Promise<Array<{ value: string; label: string; offset: string; region: string }>> {
    const response = await apiClient.get<Array<{ value: string; label: string; offset: string; region: string }>>('/settings/preferences/timezones')
    return response.data
  }

  /**
   * Get available languages
   */
  async getLanguages(): Promise<Array<{ code: string; name: string; nativeName: string; flag: string }>> {
    const response = await apiClient.get<Array<{ code: string; name: string; nativeName: string; flag: string }>>('/settings/preferences/languages')
    return response.data
  }

  /**
   * Get available currencies
   */
  async getCurrencies(): Promise<Array<{ code: string; name: string; symbol: string; flag: string }>> {
    const response = await apiClient.get<Array<{ code: string; name: string; symbol: string; flag: string }>>('/settings/preferences/currencies')
    return response.data
  }
}

// Export singleton instances
export const userSettingsApi = new UserSettingsApi()
export const businessSettingsApi = new BusinessSettingsApi()
export const taxConfigApi = new TaxConfigApi()
export const teamApi = new TeamApi()
export const categoriesApi = new CategoriesApi()
export const integrationApi = new IntegrationApi()
export const dataExportApi = new DataExportApi()
export const preferencesApi = new PreferencesApi()

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
