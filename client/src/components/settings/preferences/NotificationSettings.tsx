"use client"

import { SettingsCard } from "../SettingsCard"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { NotificationSettings as NotificationSettingsType } from "@/lib/types/settings"
import { Bell, Mail, Calendar, AlertCircle, Users, BarChart3 } from "lucide-react"

interface NotificationSettingsProps {
  settings: NotificationSettingsType
  onChange: (settings: NotificationSettingsType) => void
  disabled?: boolean
}

export function NotificationSettings({ settings, onChange, disabled }: NotificationSettingsProps) {
  const updateSetting = (key: keyof NotificationSettingsType, value: boolean) => {
    onChange({
      ...settings,
      [key]: value
    })
  }

  return (
    <SettingsCard
      title="Notifications"
      description="Configure how and when you receive notifications"
    >
      <div className="space-y-6">
        {/* Email Notifications */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center space-x-2">
            <Mail className="h-4 w-4" />
            <span>Email Notifications</span>
          </h4>
          
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="email-basic">Basic email notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Account updates and security alerts
                </p>
              </div>
              <Switch
                id="email-basic"
                checked={settings.email}
                onCheckedChange={(checked) => updateSetting('email', checked)}
                disabled={disabled}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="weekly-reports">Weekly reports</Label>
                <p className="text-sm text-muted-foreground">
                  Summary of your weekly expenses and trends
                </p>
              </div>
              <Switch
                id="weekly-reports"
                checked={settings.weeklyReports}
                onCheckedChange={(checked) => updateSetting('weeklyReports', checked)}
                disabled={disabled}
              />
            </div>
          </div>
        </div>

        {/* Push Notifications */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center space-x-2">
            <Bell className="h-4 w-4" />
            <span>Push Notifications</span>
          </h4>
          
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="push-basic">Enable push notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Real-time alerts on your device
                </p>
              </div>
              <Switch
                id="push-basic"
                checked={settings.push}
                onCheckedChange={(checked) => updateSetting('push', checked)}
                disabled={disabled}
              />
            </div>
          </div>
        </div>

        {/* Reminder Notifications */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center space-x-2">
            <Calendar className="h-4 w-4" />
            <span>Reminders</span>
          </h4>
          
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="bill-reminders">Bill reminders</Label>
                <p className="text-sm text-muted-foreground">
                  Upcoming bill due dates and payment reminders
                </p>
              </div>
              <Switch
                id="bill-reminders"
                checked={settings.billReminders}
                onCheckedChange={(checked) => updateSetting('billReminders', checked)}
                disabled={disabled}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="overdue-invoices">Overdue invoice alerts</Label>
                <p className="text-sm text-muted-foreground">
                  Notifications for overdue invoices and payments
                </p>
              </div>
              <Switch
                id="overdue-invoices"
                checked={settings.overdueInvoices}
                onCheckedChange={(checked) => updateSetting('overdueInvoices', checked)}
                disabled={disabled}
              />
            </div>
          </div>
        </div>

        {/* Team Notifications */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center space-x-2">
            <Users className="h-4 w-4" />
            <span>Team Updates</span>
          </h4>
          
          <div className="space-y-3 pl-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="team-updates">Team activity notifications</Label>
                <p className="text-sm text-muted-foreground">
                  New members, role changes, and team activities
                </p>
              </div>
              <Switch
                id="team-updates"
                checked={settings.teamUpdates}
                onCheckedChange={(checked) => updateSetting('teamUpdates', checked)}
                disabled={disabled}
              />
            </div>
          </div>
        </div>
      </div>
    </SettingsCard>
  )
} 