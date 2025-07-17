"use client"

import { useSearchParams } from "next/navigation"
import { Suspense } from "react"
import { SettingsLayout, useActiveTab } from "@/components/settings/SettingsLayout"
import { PreferencesTab } from "@/components/settings/preferences/PreferencesTab" 
import { BusinessTab } from "@/components/settings/business/BusinessTab"
import { CategoriesTab } from "@/components/settings/categories/CategoriesTab"
import { TeamTab } from "@/components/settings/team/TeamTab"
import { Skeleton } from "@/components/ui/skeleton"

// Main Settings Content Component
function SettingsContent() {
  const [activeTab] = useActiveTab()

  const renderTabContent = () => {
    switch (activeTab) {
      case 'preferences':
        return <PreferencesTab />
      case 'business':
        return <BusinessTab />
      case 'categories':
        return <CategoriesTab />
      case 'team':
        return <TeamTab />
      default:
        return <PreferencesTab />
    }
  }

  return (
    <SettingsLayout>
      {renderTabContent()}
    </SettingsLayout>
  )
}

// Loading component
function SettingsLoading() {
  return (
    <div className="space-y-6">
      {/* Sticky Header with Title and Tabs Skeletons */}
      <div className="sticky top-0 z-10 bg-background pb-4 pt-6">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-32" />
            <Skeleton className="mt-1 h-4 w-64" />
          </div>
        </div>
        <div className="mt-4">
          <Skeleton className="h-10 w-full" />
        </div>
      </div>

      {/* Content Skeletons */}
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-96 mb-6" />
          <div className="space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        </div>
      </div>
    </div>
  )
}

// Main Settings Page Component
export default function SettingsPage() {
  return (
    <Suspense fallback={<SettingsLoading />}>
      <SettingsContent />
    </Suspense>
  )
}
