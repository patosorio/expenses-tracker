"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { SettingsTab } from "@/lib/types/settings"
import { SettingsTabs } from "./SettingsTabs"

interface SettingsLayoutProps {
  children: React.ReactNode
  defaultTab?: SettingsTab
}

export function SettingsLayout({ children, defaultTab = 'preferences' }: SettingsLayoutProps) {
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState<SettingsTab>(defaultTab)

  // Initialize tab from URL params
  useEffect(() => {
    const tabParam = searchParams.get('tab') as SettingsTab
    if (tabParam && ['preferences', 'business', 'categories', 'team'].includes(tabParam)) {
      setActiveTab(tabParam)
    }
  }, [searchParams])

  return (
    <div className="space-y-6">
      {/* Sticky Header with Title and Tabs */}
      <div className="sticky top-0 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b pb-4">
        {/* Page Title */}
        <div className="mb-6">
          <h1 className="text-2xl font-light">Settings</h1>
          <p className="text-muted-foreground text-sm">Manage your account settings and preferences</p>
        </div>
        
        {/* Tab Navigation */}
        <SettingsTabs
          value={activeTab}
          onValueChange={setActiveTab}
        />
      </div>

      {/* Content */}
      <div className="space-y-6">
        {children}
      </div>
    </div>
  )
}

// Hook to get current active tab
export function useActiveTab(): [SettingsTab, (tab: SettingsTab) => void] {
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState<SettingsTab>('preferences')

  useEffect(() => {
    const tabParam = searchParams.get('tab') as SettingsTab
    if (tabParam && ['preferences', 'business', 'categories', 'team'].includes(tabParam)) {
      setActiveTab(tabParam)
    }
  }, [searchParams])

  return [activeTab, setActiveTab]
} 