"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils/utils"
import { Button } from "@/components/ui/button"
import { 
  LayoutDashboard, 
  Receipt, 
  TrendingUp, 
  ChevronLeft, 
  ChevronRight,
  Briefcase,
  PiggyBank,
  Bot,
  LineChart,
  FileText
} from "lucide-react"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Projects", href: "/dashboard/projects", icon: Briefcase },
  { name: "Budgets", href: "/dashboard/budgets", icon: PiggyBank },
  { name: "Expenses", href: "/dashboard/expenses", icon: Receipt },
  { name: "Income", href: "/dashboard/income", icon: TrendingUp },
  { name: "Forecast", href: "/dashboard/forecast", icon: LineChart },
  { name: "Reports", href: "/dashboard/reports", icon: FileText },
  { name: "AI Assistant", href: "/dashboard/ai-assistant", icon: Bot },
]

export function DashboardSidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  return (
    <div
      className={cn(
        "bg-card border-r border-border transition-all duration-300 flex flex-col",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!collapsed && <h2 className="text-lg font-light">ExpenseTracker</h2>}
          <Button variant="ghost" size="sm" onClick={() => setCollapsed(!collapsed)} className="h-8 w-8 p-0">
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      <nav className="flex-1 p-2 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link key={item.name} href={item.href}>
              <Button
                variant={isActive ? "secondary" : "ghost"}
                className={cn("w-full justify-start text-sm font-normal", collapsed && "px-2")}
              >
                <item.icon className={cn("h-4 w-4", !collapsed && "mr-3")} />
                {!collapsed && item.name}
              </Button>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
