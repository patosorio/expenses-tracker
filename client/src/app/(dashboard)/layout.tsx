"use client"

import type React from "react"
import { useState } from "react"

import { useAuth } from "@/contexts/AuthContext"
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar"
import { DashboardTopbar } from "@/components/layout/dashboard-topbar"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.push("/sign-in")
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-foreground"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen">
        <div className="fixed inset-y-0 z-50">
          <DashboardSidebar 
            collapsed={sidebarCollapsed} 
            onToggleCollapsed={() => setSidebarCollapsed(!sidebarCollapsed)} 
          />
        </div>
        <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? 'pl-16' : 'pl-64'}`}>
          <div className="sticky top-0 z-40">
            <DashboardTopbar />
          </div>
          <main className="flex-1 p-6 overflow-y-auto">{children}</main>
        </div>
      </div>
    </div>
  )
}
