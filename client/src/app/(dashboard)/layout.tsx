"use client"

import type React from "react"
import { useState } from "react"

import { RequireAuth } from "@/components/RequireAuth"
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar"
import { DashboardTopbar } from "@/components/layout/dashboard-topbar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <RequireAuth>
      <div className="min-h-screen bg-background">
        <div className="flex h-screen overflow-hidden">
          <div className="fixed inset-y-0 z-50">
            <DashboardSidebar 
              collapsed={sidebarCollapsed} 
              onToggleCollapsed={() => setSidebarCollapsed(!sidebarCollapsed)} 
            />
          </div>
          <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? 'pl-16' : 'pl-64'} min-w-0`}>
            <div className="sticky top-0 z-40">
              <DashboardTopbar />
            </div>
            <main className="flex-1 p-6 overflow-y-auto overflow-x-hidden">{children}</main>
          </div>
        </div>
      </div>
    </RequireAuth>
  )
}
