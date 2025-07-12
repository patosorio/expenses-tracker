"use client"

import { useState } from "react"
import { SettingsCard } from "../SettingsCard"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Calculator, Plus, Edit, Trash2, Star } from "lucide-react"

interface TaxConfiguration {
  id: string
  name: string
  rate: number
  code: string
  isDefault: boolean
  countryCode: string
  description?: string
}

interface TaxConfigurationSectionProps {
  configurations: TaxConfiguration[]
  onCreate: (config: Omit<TaxConfiguration, 'id'>) => Promise<void>
  onUpdate: (id: string, updates: Partial<TaxConfiguration>) => Promise<void>
  onDelete: (id: string) => Promise<void>
  loading?: boolean
}

export function TaxConfigurationSection({ 
  configurations, 
  onCreate, 
  onUpdate, 
  onDelete, 
  loading = false 
}: TaxConfigurationSectionProps) {
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [editingConfig, setEditingConfig] = useState<TaxConfiguration | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    rate: 0,
    code: "",
    isDefault: false,
    countryCode: "US",
    description: ""
  })

  const resetForm = () => {
    setFormData({
      name: "",
      rate: 0,
      code: "",
      isDefault: false,
      countryCode: "US",
      description: ""
    })
  }

  const handleCreate = async () => {
    try {
      await onCreate({
        name: formData.name,
        rate: formData.rate,
        code: formData.code,
        isDefault: formData.isDefault,
        countryCode: formData.countryCode,
        description: formData.description || undefined
      })
      setShowCreateDialog(false)
      resetForm()
    } catch (error) {
      console.error('Failed to create tax configuration:', error)
    }
  }

  const handleUpdate = async (id: string, updates: Partial<TaxConfiguration>) => {
    try {
      await onUpdate(id, updates)
    } catch (error) {
      console.error('Failed to update tax configuration:', error)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await onDelete(id)
    } catch (error) {
      console.error('Failed to delete tax configuration:', error)
    }
  }

  const handleEdit = (config: TaxConfiguration) => {
    setEditingConfig(config)
    setFormData({
      name: config.name,
      rate: config.rate,
      code: config.code,
      isDefault: config.isDefault,
      countryCode: config.countryCode,
      description: config.description || ""
    })
  }

  const handleEditSave = async () => {
    if (!editingConfig) return
    
    try {
      await onUpdate(editingConfig.id, {
        name: formData.name,
        rate: formData.rate,
        code: formData.code,
        isDefault: formData.isDefault,
        countryCode: formData.countryCode,
        description: formData.description || undefined
      })
      setEditingConfig(null)
      resetForm()
    } catch (error) {
      console.error('Failed to update tax configuration:', error)
    }
  }

  return (
    <SettingsCard
      title="Tax Configuration"
      description="Manage tax rates and configurations for your business"
      headerAction={
        <div className="flex items-center space-x-2">
          <Calculator className="h-5 w-5 text-muted-foreground" />
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button size="sm" className="flex items-center space-x-2">
                <Plus className="h-4 w-4" />
                <span>Add Tax Rate</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Tax Configuration</DialogTitle>
                <DialogDescription>
                  Add a new tax rate configuration for your business.
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="tax-name">Tax Name</Label>
                    <input
                      id="tax-name"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={formData.name}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, name: e.target.value})}
                      placeholder="e.g., Standard VAT"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="tax-rate">Tax Rate (%)</Label>
                    <input
                      id="tax-rate"
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={formData.rate}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, rate: parseFloat(e.target.value) || 0})}
                      placeholder="20.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="tax-code">Tax Code</Label>
                    <input
                      id="tax-code"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={formData.code}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, code: e.target.value})}
                      placeholder="VAT20"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="country-code">Country Code</Label>
                    <Select
                      value={formData.countryCode}
                      onValueChange={(value) => setFormData({...formData, countryCode: value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select country" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="US">United States</SelectItem>
                        <SelectItem value="GB">United Kingdom</SelectItem>
                        <SelectItem value="DE">Germany</SelectItem>
                        <SelectItem value="FR">France</SelectItem>
                        <SelectItem value="CA">Canada</SelectItem>
                        <SelectItem value="AU">Australia</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <textarea
                    id="description"
                    className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    value={formData.description}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({...formData, description: e.target.value})}
                    placeholder="Describe when this tax rate applies"
                    rows={2}
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="is-default"
                    checked={formData.isDefault}
                    onCheckedChange={(checked) => setFormData({...formData, isDefault: checked})}
                  />
                  <Label htmlFor="is-default">Set as default tax rate</Label>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={loading || !formData.name || !formData.code}>
                  Create Tax Rate
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      }
    >
      <div className="space-y-4">
        {configurations.length === 0 ? (
          <div className="text-center py-8">
            <Calculator className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No tax configurations yet</p>
            <p className="text-sm text-muted-foreground">Add your first tax rate to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {configurations.map((config) => (
              <div
                key={config.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Calculator className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{config.name}</span>
                        {config.isDefault && (
                          <Badge variant="default" className="flex items-center space-x-1">
                            <Star className="h-3 w-3" />
                            <span>Default</span>
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {config.rate}% • {config.code} • {config.countryCode}
                        {config.description && ` • ${config.description}`}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleUpdate(config.id, { isDefault: !config.isDefault })}
                    disabled={loading}
                  >
                    <Star className={`h-4 w-4 ${config.isDefault ? 'fill-current' : ''}`} />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEdit(config)}
                    disabled={loading}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(config.id)}
                    disabled={loading || config.isDefault}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Dialog */}
      <Dialog open={!!editingConfig} onOpenChange={() => setEditingConfig(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Tax Configuration</DialogTitle>
            <DialogDescription>
              Update the tax rate configuration.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="edit-tax-name">Tax Name</Label>
                <input
                  id="edit-tax-name"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={formData.name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., Standard VAT"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-tax-rate">Tax Rate (%)</Label>
                <input
                  id="edit-tax-rate"
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={formData.rate}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, rate: parseFloat(e.target.value) || 0})}
                  placeholder="20.00"
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingConfig(null)}>
              Cancel
            </Button>
            <Button onClick={handleEditSave} disabled={loading || !formData.name}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </SettingsCard>
  )
} 