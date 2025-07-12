"use client"

import { useSearchParams } from "next/navigation"
import { Suspense } from "react"
import { SettingsLayout, useActiveTab } from "@/components/settings/SettingsLayout"
import { PreferencesTab } from "@/components/settings/preferences/PreferencesTab" 
import { BusinessTab } from "@/components/settings/business/BusinessTab"
import { SettingsCard } from "@/components/settings/SettingsCard"
import { LucideIconPicker } from "@/components/settings/LucideIconPicker"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { SettingsTab as SettingsTabType } from "@/lib/types/settings"
import { 
  FolderTree, 
  Users, 
  Plus, 
  Edit, 
  Trash2, 
  Star,
  UserPlus,
  Mail,
  Shield,
  MoreHorizontal
} from "lucide-react"

// Category Management Tab Component (simplified for now)
function CategoriesTab() {
  const mockCategories = [
    { id: "1", name: "Food & Dining", icon: "utensils", color: "#10B981", type: "expense" as const },
    { id: "2", name: "Transportation", icon: "car", color: "#3B82F6", type: "expense" as const },
    { id: "3", name: "Salary", icon: "dollar-sign", color: "#8B5CF6", type: "income" as const },
  ]

  return (
    <div className="space-y-6">
      <SettingsCard
        title="Categories"
        description="Organize your expenses and income with custom categories"
        headerAction={
          <Button size="sm" className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Add Category</span>
          </Button>
        }
      >
        <div className="space-y-4">
          <div className="grid gap-4">
            {mockCategories.map((category) => (
              <div
                key={category.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white"
                    style={{ backgroundColor: category.color }}
                  >
                    <FolderTree className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{category.name}</span>
                      <Badge variant={category.type === 'expense' ? 'destructive' : 'default'}>
                        {category.type}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {category.icon} • Used in 12 transactions
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="sm">
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center py-6 border-2 border-dashed border-muted rounded-lg">
            <FolderTree className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-2">Create your first category</p>
            <p className="text-sm text-muted-foreground mb-4">
              Organize your expenses and income for better tracking
            </p>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Category
            </Button>
          </div>
        </div>
      </SettingsCard>
    </div>
  )
}

// Team Management Tab Component (simplified for now)
function TeamTab() {
  const mockTeamMembers = [
    { 
      id: "1", 
      email: "john.doe@company.com", 
      name: "John Doe", 
      role: "admin" as const, 
      status: "active" as const,
      invitedAt: "2024-01-15",
      lastActive: "2 hours ago"
    },
    { 
      id: "2", 
      email: "jane.smith@company.com", 
      name: "Jane Smith", 
      role: "user" as const, 
      status: "pending" as const,
      invitedAt: "2024-12-01"
    },
  ]

  return (
    <div className="space-y-6">
      <SettingsCard
        title="Team Members"
        description="Manage team access and permissions"
        headerAction={
          <Button size="sm" className="flex items-center space-x-2">
            <UserPlus className="h-4 w-4" />
            <span>Invite Member</span>
          </Button>
        }
      >
        <div className="space-y-4">
          {mockTeamMembers.map((member) => (
            <div
              key={member.id}
              className="flex items-center justify-between p-4 border rounded-lg"
            >
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium">
                    {member.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">{member.name}</span>
                    <Badge variant={member.role === 'admin' ? 'default' : 'secondary'}>
                      {member.role}
                    </Badge>
                    <Badge 
                      variant={member.status === 'active' ? 'default' : 'secondary'}
                      className={member.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : ''}
                    >
                      {member.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {member.email} • Invited {member.invitedAt}
                    {member.lastActive && ` • Last active ${member.lastActive}`}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}

          <div className="text-center py-6 border-2 border-dashed border-muted rounded-lg">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-2">Invite your team</p>
            <p className="text-sm text-muted-foreground mb-4">
              Collaborate on expense management with your team members
            </p>
            <Button>
              <Mail className="h-4 w-4 mr-2" />
              Send Invitation
            </Button>
          </div>
        </div>
      </SettingsCard>

      <SettingsCard
        title="Roles & Permissions"
        description="Configure access levels for team members"
      >
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            {[
              { role: 'Admin', icon: Shield, description: 'Full access to all features', color: 'bg-red-100 text-red-800' },
              { role: 'User', icon: Users, description: 'Can manage expenses and view reports', color: 'bg-blue-100 text-blue-800' },
              { role: 'Viewer', icon: Star, description: 'Read-only access to reports', color: 'bg-gray-100 text-gray-800' }
            ].map((role) => {
              const Icon = role.icon
              return (
                <div key={role.role} className="p-4 border rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{role.role}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {role.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </SettingsCard>
    </div>
  )
}

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
      <div className="sticky top-0 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b pb-4">
        {/* Page Title Skeleton */}
        <div className="mb-6 space-y-2">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-64" />
        </div>
        
        {/* Tab Navigation Skeleton */}
        <div className="space-y-4">
          <div className="grid w-full grid-cols-4 bg-muted/50 rounded-lg p-1">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 rounded-md" />
            ))}
          </div>
          <div className="text-center">
            <Skeleton className="h-4 w-48 mx-auto" />
          </div>
        </div>
      </div>

      {/* Content Skeletons */}
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

// Main Settings Page Component
export default function SettingsPage() {
  return (
    <Suspense fallback={<SettingsLoading />}>
      <SettingsContent />
    </Suspense>
  )
}
