"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils/utils"

interface SettingsCardProps {
  title: string
  description?: string
  children: React.ReactNode
  className?: string
  headerAction?: React.ReactNode
  size?: 'default' | 'large'
}

export function SettingsCard({
  title,
  description,
  children,
  className,
  headerAction,
  size = 'default'
}: SettingsCardProps) {
  return (
    <Card className={cn("", className)}>
      <CardHeader className={cn(
        "space-y-1",
        size === 'large' ? "pb-6" : "pb-4"
      )}>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className={cn(
              "font-light",
              size === 'large' ? "text-xl" : "text-lg"
            )}>
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-sm text-muted-foreground">
                {description}
              </CardDescription>
            )}
          </div>
          {headerAction && (
            <div className="flex items-center space-x-2">
              {headerAction}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className={cn(
        "space-y-4",
        size === 'large' ? "pt-0" : "pt-0"
      )}>
        {children}
      </CardContent>
    </Card>
  )
} 