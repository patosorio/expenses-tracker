"use client"

import { useState, useEffect } from "react"
import { SettingsCard } from "../SettingsCard"
import { TaxConfigurationSection } from "@/components/settings/business/TaxConfigurationSection"
import { BusinessInfoSection } from "@/components/settings/business/BusinessInfoSection"
import { IntegrationSettings } from "@/components/settings/business/IntegrationSettings"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"

interface BusinessSettings {
  companyName: string
  taxId: string
  fiscalYearStart: string
  defaultCurrency: string
  address: string
  phone: string
  email: string
}

interface TaxConfiguration {
  id: string
  name: string
  rate: number
  code: string
  isDefault: boolean
  countryCode: string
  description?: string
}

export function BusinessTab() {
  const [businessSettings, setBusinessSettings] = useState<BusinessSettings | null>(null)
  const [taxConfigurations, setTaxConfigurations] = useState<TaxConfiguration[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Load business settings on mount
  useEffect(() => {
    loadBusinessSettings()
  }, [])

  const loadBusinessSettings = async () => {
    try {
      setLoading(true)
      // Simulate API calls
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Set default business settings
      setBusinessSettings({
        companyName: "My Company",
        taxId: "",
        fiscalYearStart: "01-01",
        defaultCurrency: "USD",
        address: "",
        phone: "",
        email: ""
      })

      // Set default tax configurations
      setTaxConfigurations([
        {
          id: "1",
          name: "Standard VAT",
          rate: 20,
          code: "VAT20",
          isDefault: true,
          countryCode: "US",
          description: "Standard VAT rate"
        },
        {
          id: "2", 
          name: "Reduced VAT",
          rate: 5,
          code: "VAT5",
          isDefault: false,
          countryCode: "US",
          description: "Reduced VAT rate for essential goods"
        }
      ])
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load business settings.' })
    } finally {
      setLoading(false)
    }
  }

  const updateBusinessSettings = (updates: Partial<BusinessSettings>) => {
    if (!businessSettings) return
    setBusinessSettings({ ...businessSettings, ...updates })
  }

  const saveBusinessSettings = async (settings: BusinessSettings) => {
    try {
      setSaving(true)
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setBusinessSettings(settings)
      setMessage({ type: 'success', text: 'Business settings saved successfully!' })
      
      // Clear message after 3 seconds
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save business settings.' })
    } finally {
      setSaving(false)
    }
  }

  const createTaxConfiguration = async (config: Omit<TaxConfiguration, 'id'>) => {
    try {
      setSaving(true)
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const newConfig = {
        ...config,
        id: Date.now().toString()
      }
      
      setTaxConfigurations([...taxConfigurations, newConfig])
      setMessage({ type: 'success', text: 'Tax configuration created successfully!' })
      
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create tax configuration.' })
    } finally {
      setSaving(false)
    }
  }

  const updateTaxConfiguration = async (id: string, updates: Partial<TaxConfiguration>) => {
    try {
      setSaving(true)
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setTaxConfigurations(prev => 
        prev.map(config => 
          config.id === id ? { ...config, ...updates } : config
        )
      )
      
      setMessage({ type: 'success', text: 'Tax configuration updated successfully!' })
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update tax configuration.' })
    } finally {
      setSaving(false)
    }
  }

  const deleteTaxConfiguration = async (id: string) => {
    try {
      setSaving(true)
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setTaxConfigurations(prev => prev.filter(config => config.id !== id))
      setMessage({ type: 'success', text: 'Tax configuration deleted successfully!' })
      
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to delete tax configuration.' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <SettingsCard key={i} title="" description="">
            <div className="space-y-4">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          </SettingsCard>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Message Display */}
      {message && (
        <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      {/* Business Information */}
      {businessSettings && (
        <BusinessInfoSection
          settings={businessSettings}
          onSave={saveBusinessSettings}
          loading={saving}
        />
      )}

      {/* Tax Configuration */}
      <TaxConfigurationSection
        configurations={taxConfigurations}
        onCreate={createTaxConfiguration}
        onUpdate={updateTaxConfiguration}
        onDelete={deleteTaxConfiguration}
        loading={saving}
      />

      {/* Integration Settings */}
      <IntegrationSettings />
    </div>
  )
} 