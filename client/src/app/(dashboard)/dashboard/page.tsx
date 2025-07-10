"use client"

import { Card, CardContent} from "@/components/ui/card"
import { useAuth } from "@/lib/contexts/AuthContext"

export default function DashboardPage() {
  const { loading } = useAuth()

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse space-y-2">
                  <div className="h-4 bg-muted rounded w-1/2"></div>
                  <div className="h-8 bg-muted rounded w-3/4"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-light">Dashboard</h1>
        <p className="text-muted-foreground text-sm">Overview of your household expenses</p>
      </div>
    </div>
  )
}
