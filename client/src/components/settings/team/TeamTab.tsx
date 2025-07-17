import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { SettingsCard } from "@/components/settings/SettingsCard"
import { 
  Users,
  UserPlus,
  Mail,
  Shield,
  Star,
  MoreHorizontal
} from "lucide-react"

export function TeamTab() {
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