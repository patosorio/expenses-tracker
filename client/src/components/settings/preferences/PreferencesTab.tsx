"use client"

import { useState, useEffect } from "react"
import { SettingsCard } from "../SettingsCard"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Save, RotateCcw, Sun, Moon, Monitor } from "lucide-react"

interface UserSettings {
  timezone: string
  language: string
  currency: string
  dateFormat: string
  theme: 'light' | 'dark' | 'system'
  notifications: {
    email: boolean
    push: boolean
    billReminders: boolean
    weeklyReports: boolean
    overdueInvoices: boolean
    teamUpdates: boolean
  }
}

export function PreferencesTab() {
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Load user settings on mount
  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setLoading(true)
      // Simulate API call - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Set default settings for now
      setSettings({
        timezone: "UTC",
        language: "en",
        currency: "USD",
        dateFormat: "MM/DD/YYYY",
        theme: "system",
        notifications: {
          email: true,
          push: true,
          billReminders: true,
          weeklyReports: false,
          overdueInvoices: true,
          teamUpdates: true,
        }
      })
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load settings. Using defaults.' })
      // Set default settings
      setSettings({
        timezone: "UTC",
        language: "en",
        currency: "USD",
        dateFormat: "MM/DD/YYYY",
        theme: "system",
        notifications: {
          email: true,
          push: true,
          billReminders: true,
          weeklyReports: false,
          overdueInvoices: true,
          teamUpdates: true,
        }
      })
    } finally {
      setLoading(false)
    }
  }

  const updateSettings = (updates: Partial<UserSettings>) => {
    if (!settings) return
    
    const newSettings = { ...settings, ...updates }
    setSettings(newSettings)
    setHasChanges(true)
  }

  const updateNotifications = (notificationUpdates: Partial<UserSettings['notifications']>) => {
    if (!settings) return
    
    const newNotifications = { ...settings.notifications, ...notificationUpdates }
    updateSettings({ notifications: newNotifications })
  }

  const saveSettings = async () => {
    if (!settings || !hasChanges) return

    try {
      setSaving(true)
      // Simulate API call - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setHasChanges(false)
      setMessage({ type: 'success', text: 'Settings saved successfully!' })
      
      // Clear message after 3 seconds
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save settings. Please try again.' })
    } finally {
      setSaving(false)
    }
  }

  const resetSettings = async () => {
    try {
      setSaving(true)
      // Simulate API call - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      await loadSettings()
      setHasChanges(false)
      setMessage({ type: 'success', text: 'Settings reset to defaults.' })
      
      // Clear message after 3 seconds
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to reset settings. Please try again.' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <SettingsCard key={i} title="" description="">
            <div className="space-y-4">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-10 w-full" />
            </div>
          </SettingsCard>
        ))}
      </div>
    )
  }

  if (!settings) {
    return (
      <div className="space-y-6">
        <SettingsCard title="Error" description="Failed to load settings">
          <Button onClick={loadSettings} variant="outline">
            Try Again
          </Button>
        </SettingsCard>
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

      {/* Regional Settings */}
      <SettingsCard
        title="Regional Settings"
        description="Configure your location, language, and date format preferences"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Select
              value={settings.language}
              onValueChange={(language: string) => updateSettings({ language })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">🇺🇸 English</SelectItem>
                <SelectItem value="es">🇪🇸 Spanish</SelectItem>
                <SelectItem value="fr">🇫🇷 French</SelectItem>
                <SelectItem value="de">🇩🇪 German</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <Select
              value={settings.timezone}
              onValueChange={(timezone: string) => updateSettings({ timezone })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select timezone" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="UTC">UTC</SelectItem>
                <SelectItem value="America/New_York">Eastern Time</SelectItem>
                <SelectItem value="America/Chicago">Central Time</SelectItem>
                <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                <SelectItem value="Europe/London">London</SelectItem>
                <SelectItem value="Europe/Paris">Paris</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="currency">Default Currency</Label>
            <Select
              value={settings.currency}
              onValueChange={(currency: string) => updateSettings({ currency })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select currency" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="USD">USD - US Dollar</SelectItem>
                <SelectItem value="EUR">EUR - Euro</SelectItem>
                <SelectItem value="GBP">GBP - British Pound</SelectItem>
                <SelectItem value="CAD">CAD - Canadian Dollar</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="dateFormat">Date Format</Label>
            <Select
              value={settings.dateFormat}
              onValueChange={(dateFormat: string) => updateSettings({ dateFormat })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select date format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </SettingsCard>

      {/* Theme Settings */}
      <SettingsCard
        title="Appearance"
        description="Customize the look and feel of your interface"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { value: 'light', label: 'Light', icon: Sun },
              { value: 'dark', label: 'Dark', icon: Moon },
              { value: 'system', label: 'System', icon: Monitor }
            ].map((option) => {
              const Icon = option.icon
              const isSelected = settings.theme === option.value
              
              return (
                <Button
                  key={option.value}
                  variant={isSelected ? "default" : "outline"}
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={() => updateSettings({ theme: option.value as 'light' | 'dark' | 'system' })}
                >
                  <Icon className="h-6 w-6" />
                  <span>{option.label}</span>
                </Button>
              )
            })}
          </div>
        </div>
      </SettingsCard>

      {/* Notification Settings */}
      <SettingsCard
        title="Notifications"
        description="Configure how and when you receive notifications"
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="email">Email notifications</Label>
              <p className="text-sm text-muted-foreground">Account updates and security alerts</p>
            </div>
            <Switch
              id="email"
              checked={settings.notifications.email}
              onCheckedChange={(checked) => updateNotifications({ email: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="push">Push notifications</Label>
              <p className="text-sm text-muted-foreground">Real-time alerts on your device</p>
            </div>
            <Switch
              id="push"
              checked={settings.notifications.push}
              onCheckedChange={(checked) => updateNotifications({ push: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="billReminders">Bill reminders</Label>
              <p className="text-sm text-muted-foreground">Upcoming bill due dates</p>
            </div>
            <Switch
              id="billReminders"
              checked={settings.notifications.billReminders}
              onCheckedChange={(checked) => updateNotifications({ billReminders: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="weeklyReports">Weekly reports</Label>
              <p className="text-sm text-muted-foreground">Summary of your weekly expenses</p>
            </div>
            <Switch
              id="weeklyReports"
              checked={settings.notifications.weeklyReports}
              onCheckedChange={(checked) => updateNotifications({ weeklyReports: checked })}
            />
          </div>
        </div>
      </SettingsCard>

      {/* Save/Reset Actions */}
      <SettingsCard
        title="Actions"
        description="Save your changes or reset to default preferences"
      >
        <div className="flex items-center space-x-4">
          <Button
            onClick={saveSettings}
            disabled={!hasChanges || saving}
            className="flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>
              {saving ? "Saving..." : "Save Changes"}
            </span>
          </Button>
          
          <Button
            variant="outline"
            onClick={resetSettings}
            disabled={saving}
            className="flex items-center space-x-2"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Reset to Defaults</span>
          </Button>
          
          {hasChanges && (
            <p className="text-sm text-muted-foreground">
              You have unsaved changes
            </p>
          )}
        </div>
      </SettingsCard>
    </div>
  )
} 