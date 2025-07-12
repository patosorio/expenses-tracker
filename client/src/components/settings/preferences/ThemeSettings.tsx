"use client"

import { SettingsCard } from "../SettingsCard"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Sun, Moon, Monitor } from "lucide-react"

interface ThemeSettingsProps {
  value: 'light' | 'dark' | 'system'
  onChange: (theme: 'light' | 'dark' | 'system') => void
  disabled?: boolean
}

export function ThemeSettings({ value, onChange, disabled }: ThemeSettingsProps) {
  const themeOptions = [
    {
      value: 'light' as const,
      label: 'Light',
      description: 'Light theme with white backgrounds',
      icon: Sun
    },
    {
      value: 'dark' as const,
      label: 'Dark',
      description: 'Dark theme with dark backgrounds',
      icon: Moon
    },
    {
      value: 'system' as const,
      label: 'System',
      description: 'Follow your system preference',
      icon: Monitor
    }
  ]

  return (
    <SettingsCard
      title="Appearance"
      description="Customize the look and feel of your interface"
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="theme">Theme</Label>
          <p className="text-sm text-muted-foreground">
            Choose how the interface appears to you
          </p>
        </div>

        {/* Theme Options as Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {themeOptions.map((option) => {
            const Icon = option.icon
            const isSelected = value === option.value
            
            return (
              <Button
                key={option.value}
                variant={isSelected ? "default" : "outline"}
                className="h-auto p-4 flex flex-col items-center space-y-2"
                onClick={() => onChange(option.value)}
                disabled={disabled}
              >
                <Icon className="h-6 w-6" />
                <div className="text-center">
                  <div className="font-medium">{option.label}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {option.description}
                  </div>
                </div>
              </Button>
            )
          })}
        </div>

        {/* Alternative: Dropdown selector */}
        <div className="space-y-2">
          <Label htmlFor="theme-select">Or use dropdown</Label>
          <Select value={value} onValueChange={onChange} disabled={disabled}>
            <SelectTrigger id="theme-select">
              <SelectValue placeholder="Select theme" />
            </SelectTrigger>
            <SelectContent>
              {themeOptions.map((option) => {
                const Icon = option.icon
                return (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex items-center space-x-2">
                      <Icon className="h-4 w-4" />
                      <span>{option.label}</span>
                    </div>
                  </SelectItem>
                )
              })}
            </SelectContent>
          </Select>
        </div>

        {value === 'system' && (
          <div className="bg-muted/50 p-3 rounded-md">
            <p className="text-sm text-muted-foreground">
              <Monitor className="h-4 w-4 inline mr-1" />
              System theme will automatically switch between light and dark based on your operating system settings.
            </p>
          </div>
        )}
      </div>
    </SettingsCard>
  )
} 