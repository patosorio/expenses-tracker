"use client"

import { useState } from "react"
import { SettingsCard } from "../SettingsCard"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Building2, Save } from "lucide-react"

interface BusinessSettings {
  companyName: string
  taxId: string
  fiscalYearStart: string
  defaultCurrency: string
  address: string
  phone: string
  email: string
}

interface BusinessInfoSectionProps {
  settings: BusinessSettings
  onSave: (settings: BusinessSettings) => Promise<void>
  loading?: boolean
}

export function BusinessInfoSection({ settings, onSave, loading = false }: BusinessInfoSectionProps) {
  const [formData, setFormData] = useState<BusinessSettings>(settings)
  const [hasChanges, setHasChanges] = useState(false)

  const updateField = (field: keyof BusinessSettings, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setHasChanges(true)
  }

  const handleSave = async () => {
    await onSave(formData)
    setHasChanges(false)
  }

  const handleReset = () => {
    setFormData(settings)
    setHasChanges(false)
  }

  return (
    <SettingsCard
      title="Company Information"
      description="Basic company details and business configuration"
      headerAction={
        <Building2 className="h-5 w-5 text-muted-foreground" />
      }
    >
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="companyName">Company Name</Label>
            <input
              id="companyName"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={formData.companyName}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('companyName', e.target.value)}
              placeholder="Enter company name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="taxId">Tax ID / EIN</Label>
            <input
              id="taxId"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={formData.taxId}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('taxId', e.target.value)}
              placeholder="Enter tax identification number"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Business Email</Label>
            <input
              id="email"
              type="email"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={formData.email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('email', e.target.value)}
              placeholder="business@company.com"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Business Phone</Label>
            <input
              id="phone"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={formData.phone}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('phone', e.target.value)}
              placeholder="(555) 123-4567"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="defaultCurrency">Default Currency</Label>
            <Select
              value={formData.defaultCurrency}
              onValueChange={(value) => updateField('defaultCurrency', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select currency" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="USD">USD - US Dollar</SelectItem>
                <SelectItem value="EUR">EUR - Euro</SelectItem>
                <SelectItem value="GBP">GBP - British Pound</SelectItem>
                <SelectItem value="CAD">CAD - Canadian Dollar</SelectItem>
                <SelectItem value="AUD">AUD - Australian Dollar</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="fiscalYearStart">Fiscal Year Start</Label>
            <Select
              value={formData.fiscalYearStart}
              onValueChange={(value) => updateField('fiscalYearStart', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select month" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="01-01">January</SelectItem>
                <SelectItem value="02-01">February</SelectItem>
                <SelectItem value="03-01">March</SelectItem>
                <SelectItem value="04-01">April</SelectItem>
                <SelectItem value="05-01">May</SelectItem>
                <SelectItem value="06-01">June</SelectItem>
                <SelectItem value="07-01">July</SelectItem>
                <SelectItem value="08-01">August</SelectItem>
                <SelectItem value="09-01">September</SelectItem>
                <SelectItem value="10-01">October</SelectItem>
                <SelectItem value="11-01">November</SelectItem>
                <SelectItem value="12-01">December</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="address">Business Address</Label>
          <textarea
            id="address"
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            value={formData.address}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => updateField('address', e.target.value)}
            placeholder="Enter full business address"
            rows={3}
          />
        </div>

        <div className="flex items-center space-x-4">
          <Button
            onClick={handleSave}
            disabled={!hasChanges || loading}
            className="flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>{loading ? "Saving..." : "Save Changes"}</span>
          </Button>

          {hasChanges && (
            <Button
              variant="outline"
              onClick={handleReset}
              disabled={loading}
            >
              Reset
            </Button>
          )}

          {hasChanges && (
            <p className="text-sm text-muted-foreground">
              You have unsaved changes
            </p>
          )}
        </div>
      </div>
    </SettingsCard>
  )
} 