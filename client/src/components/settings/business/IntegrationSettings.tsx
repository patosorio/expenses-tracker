"use client"

import { useState } from "react"
import { SettingsCard } from "../SettingsCard"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Settings, Plus, Key, Trash2, Eye, EyeOff, ExternalLink, CheckCircle, XCircle } from "lucide-react"

interface ApiKey {
  id: string
  name: string
  service: string
  isActive: boolean
  createdAt: string
  lastUsed?: string
  keyPreview: string
}

export function IntegrationSettings() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    {
      id: "1",
      name: "Stripe Payment Processing",
      service: "Stripe",
      isActive: true,
      createdAt: "2024-01-15",
      lastUsed: "2024-12-01",
      keyPreview: "sk_test_****7890"
    },
    {
      id: "2",
      name: "QuickBooks Integration",
      service: "QuickBooks",
      isActive: false,
      createdAt: "2024-02-10",
      keyPreview: "qb_****abcd"
    }
  ])

  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showKeyValue, setShowKeyValue] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    service: "",
    apiKey: ""
  })

  const resetForm = () => {
    setFormData({ name: "", service: "", apiKey: "" })
  }

  const handleCreateApiKey = () => {
    const newApiKey: ApiKey = {
      id: Date.now().toString(),
      name: formData.name,
      service: formData.service,
      isActive: true,
      createdAt: new Date().toISOString().split('T')[0],
      keyPreview: `****${formData.apiKey.slice(-4)}`
    }

    setApiKeys([...apiKeys, newApiKey])
    setShowCreateDialog(false)
    resetForm()
  }

  const handleDeleteApiKey = (id: string) => {
    setApiKeys(apiKeys.filter(key => key.id !== id))
  }

  const handleToggleStatus = (id: string) => {
    setApiKeys(apiKeys.map(key => 
      key.id === id ? { ...key, isActive: !key.isActive } : key
    ))
  }

  const integrationOptions = [
    {
      name: "Stripe",
      description: "Payment processing and subscription management",
      status: "connected",
      icon: "💳"
    },
    {
      name: "QuickBooks",
      description: "Accounting and bookkeeping integration",
      status: "available",
      icon: "📊"
    },
    {
      name: "Xero",
      description: "Cloud-based accounting software",
      status: "available",
      icon: "📋"
    },
    {
      name: "PayPal",
      description: "Alternative payment processing",
      status: "available",
      icon: "🏦"
    }
  ]

  return (
    <SettingsCard
      title="Integrations & API Keys"
      description="Manage third-party integrations and API credentials"
      headerAction={
        <Settings className="h-5 w-5 text-muted-foreground" />
      }
    >
      <div className="space-y-6">
        {/* Available Integrations */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium">Available Integrations</h4>
          <div className="grid gap-4 md:grid-cols-2">
            {integrationOptions.map((integration) => (
              <div
                key={integration.name}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{integration.icon}</span>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{integration.name}</span>
                      {integration.status === 'connected' ? (
                        <Badge variant="default" className="flex items-center space-x-1">
                          <CheckCircle className="h-3 w-3" />
                          <span>Connected</span>
                        </Badge>
                      ) : (
                        <Badge variant="secondary">Available</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {integration.description}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {integration.status === 'connected' ? (
                    <Button variant="outline" size="sm">
                      Configure
                    </Button>
                  ) : (
                    <Button size="sm">
                      Connect
                    </Button>
                  )}
                  <Button variant="ghost" size="sm">
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* API Keys Management */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">API Keys</h4>
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button size="sm" className="flex items-center space-x-2">
                  <Plus className="h-4 w-4" />
                  <span>Add API Key</span>
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add API Key</DialogTitle>
                  <DialogDescription>
                    Add a new API key for third-party service integration.
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="key-name">Key Name</Label>
                    <input
                      id="key-name"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={formData.name}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, name: e.target.value})}
                      placeholder="e.g., Stripe Production Key"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="service">Service</Label>
                    <input
                      id="service"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={formData.service}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, service: e.target.value})}
                      placeholder="e.g., Stripe"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="api-key">API Key</Label>
                    <input
                      id="api-key"
                      type="password"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={formData.apiKey}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, apiKey: e.target.value})}
                      placeholder="Enter your API key"
                    />
                  </div>

                  <Alert>
                    <Key className="h-4 w-4" />
                    <AlertDescription>
                      API keys are encrypted and stored securely. Only the last 4 characters will be visible after saving.
                    </AlertDescription>
                  </Alert>
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleCreateApiKey} 
                    disabled={!formData.name || !formData.service || !formData.apiKey}
                  >
                    Add API Key
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {apiKeys.length === 0 ? (
            <div className="text-center py-8">
              <Key className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No API keys configured</p>
              <p className="text-sm text-muted-foreground">Add your first API key to enable integrations</p>
            </div>
          ) : (
            <div className="space-y-3">
              {apiKeys.map((apiKey) => (
                <div
                  key={apiKey.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <Key className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{apiKey.name}</span>
                        {apiKey.isActive ? (
                          <Badge variant="default" className="flex items-center space-x-1">
                            <CheckCircle className="h-3 w-3" />
                            <span>Active</span>
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="flex items-center space-x-1">
                            <XCircle className="h-3 w-3" />
                            <span>Inactive</span>
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {apiKey.service} • {apiKey.keyPreview} • Created {apiKey.createdAt}
                        {apiKey.lastUsed && ` • Last used ${apiKey.lastUsed}`}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowKeyValue(showKeyValue === apiKey.id ? null : apiKey.id)}
                    >
                      {showKeyValue === apiKey.id ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleStatus(apiKey.id)}
                    >
                      {apiKey.isActive ? 'Disable' : 'Enable'}
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteApiKey(apiKey.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Webhook Settings */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium">Webhook Configuration</h4>
          <div className="p-4 border rounded-lg bg-muted/50">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h5 className="font-medium">Webhook Endpoint</h5>
                <p className="text-sm text-muted-foreground">
                  Configure webhook URLs for real-time notifications
                </p>
              </div>
              <Button variant="outline" size="sm">
                Configure
              </Button>
            </div>
            
            <div className="space-y-2">
              <Label>Current Endpoint</Label>
              <div className="flex items-center space-x-2">
                <code className="bg-background px-2 py-1 rounded text-sm">
                  https://api.yourapp.com/webhooks/payments
                </code>
                <Button variant="ghost" size="sm">
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SettingsCard>
  )
} 