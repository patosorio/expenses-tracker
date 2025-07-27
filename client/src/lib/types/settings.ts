// User Settings Types
export interface UserSettings {
  timezone: string
  language: string
  currency: string
  dateFormat: string
  notifications: NotificationSettings
  theme: 'light' | 'dark' | 'system'
}

export interface NotificationSettings {
  email: boolean
  push: boolean
  billReminders: boolean
  weeklyReports: boolean
  overdueInvoices: boolean
  teamUpdates: boolean
}

// Business Settings Types
export interface BusinessSettings {
  company_name: string
  tax_id: string
  fiscal_year_start: string
  default_currency: string
  tax_configurations: TaxConfiguration[]
}

export interface TaxConfiguration {
  id: string
  name: string
  rate: number
  code: string
  is_default: boolean
  country_code: string
  description?: string
}

export interface TaxConfigurationCreate {
  name: string
  rate: number
  code: string
  is_default: boolean
  country_code: string
  description?: string
}

export interface TaxConfigurationUpdate {
  name?: string
  rate?: number
  code?: string
  is_default?: boolean
  country_code?: string
  description?: string
}

// Team Management Types
export interface TeamMember {
  id: string
  email: string
  name: string
  role: 'admin' | 'user' | 'viewer'
  status: 'active' | 'pending' | 'inactive'
  invited_at: string
  last_active?: string
}

export interface TeamInvitation {
  email: string
  role: 'admin' | 'user' | 'viewer'
  message?: string
}

// Category Types
export interface CategoryFormData {
  name: string
  type: 'expense' | 'income'
  color: string
  icon: string
  parent_id?: string
  is_default: boolean
}

export interface Category {
  id: string
  name: string
  type: 'expense' | 'income'
  color: string
  icon: string
  parent_id?: string
  is_default: boolean
  level: number
  user_id: string
  created_at: string
  updated_at?: string
  is_active: boolean
}


export interface CategoryWithChildren extends Category {
  children: CategoryWithChildren[]
}

export interface CategoryHierarchy {
  id: string
  name: string
  type: 'expense' | 'income'
  color: string
  icon: string
  level: number
  path: string[]
  children: CategoryHierarchy[]
}

// Settings Tab Types
export type SettingsTab = 'preferences' | 'business' | 'categories' | 'team'

// Integration Settings Types
export interface IntegrationSettings {
  apiKeys: ApiKeyConfiguration[]
  webhooks: WebhookConfiguration[]
  exports: ExportConfiguration
}

export interface ApiKeyConfiguration {
  id: string
  name: string
  service: string
  is_active: boolean
  created_at: string
  last_used?: string
}

export interface WebhookConfiguration {
  id: string
  url: string
  events: string[]
  is_active: boolean
  secret: string
}

export interface ExportConfiguration {
  auto_export: boolean
  frequency: 'daily' | 'weekly' | 'monthly'
  format: 'csv' | 'pdf' | 'json'
  destination: 'email' | 'drive' | 'local'
  recipients: string[]
}

// Form Types
export interface UserSettingsUpdate {
  timezone?: string
  language?: string
  currency?: string
  dateFormat?: string
  notifications?: Partial<NotificationSettings>
  theme?: 'light' | 'dark' | 'system'
}

export interface BusinessSettingsUpdate {
  company_name?: string
  tax_id?: string
  fiscal_year_start?: string
  default_currency?: string
}

// Response Types
export interface SettingsResponse<T> {
  data: T
  success: boolean
  message?: string
}

export interface SettingsError {
  field?: string
  message: string
  code?: string
}

// Icon Types
export interface IconData {
  name: string
  component: React.ComponentType<any>
  categories: string[]
  tags: string[]
}

export interface IconPickerProps {
  value?: string
  onChange: (iconName: string) => void
  categories?: string[]
  placeholder?: string
}

// Timezone Types
export interface TimezoneOption {
  value: string
  label: string
  offset: string
  region: string
}

// Language Types
export interface LanguageOption {
  code: string
  name: string
  nativeName: string
  flag: string
}

// Currency Types
export interface CurrencyOption {
  code: string
  name: string
  symbol: string
  flag: string
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export interface LoadingState {
  isLoading: boolean
  error?: string
  lastUpdated?: string
}

export interface FormState<T> extends LoadingState {
  data: T
  isDirty: boolean
  hasChanges: boolean
}
