"use client"

import { useRouter, useSearchParams } from "next/navigation"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SettingsTab } from "@/types/settings"
import { 
  User, 
  Building2, 
  FolderTree, 
  Users,
  Settings,
  Palette,
  DollarSign,
  Globe
} from "lucide-react"

interface SettingsTabConfig {
  value: SettingsTab
  label: string
  icon: React.ComponentType<any>
  description: string
}

const tabsConfig: SettingsTabConfig[] = [
  {
    value: 'preferences',
    label: 'Preferences',
    icon: User,
    description: 'Personal settings and preferences'
  },
  {
    value: 'business',
    label: 'Business',
    icon: Building2,
    description: 'Company and tax settings'
  },
  {
    value: 'categories',
    label: 'Categories',
    icon: FolderTree,
    description: 'Manage expense and income categories'
  },
  {
    value: 'team',
    label: 'Team',
    icon: Users,
    description: 'Team members and permissions'
  }
]

interface SettingsTabsProps {
  value: SettingsTab
  onValueChange: (value: SettingsTab) => void
  className?: string
}

export function SettingsTabs({ value, onValueChange, className }: SettingsTabsProps) {
  const router = useRouter()
  const searchParams = useSearchParams()

  const handleTabChange = (newValue: string) => {
    const tab = newValue as SettingsTab
    onValueChange(tab)
    
    // Update URL with new tab
    const params = new URLSearchParams(searchParams)
    params.set('tab', tab)
    router.push(`/settings?${params.toString()}`, { scroll: false })
  }

  return (
    <div className={className}>
      <Tabs value={value} onValueChange={handleTabChange} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 bg-muted/50">
          {tabsConfig.map((tab) => {
            const Icon = tab.icon
            return (
              <TabsTrigger
                key={tab.value}
                value={tab.value}
                className="flex items-center space-x-2 data-[state=active]:bg-background data-[state=active]:shadow-sm"
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </TabsTrigger>
            )
          })}
        </TabsList>
        
        {/* Tab descriptions */}
        <div className="text-center">
          {tabsConfig.map((tab) => {
            if (tab.value === value) {
              return (
                <p key={tab.value} className="text-sm text-muted-foreground">
                  {tab.description}
                </p>
              )
            }
            return null
          })}
        </div>
      </Tabs>
    </div>
  )
}

export { tabsConfig }
export type { SettingsTabConfig } 