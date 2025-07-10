"use client"

import type React from "react"
import { cn } from "@/lib/utils/utils"

interface FloatingInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

export function FloatingInput({ label, error, className, ...props }: FloatingInputProps) {
  return (
    <div className="floating-label-group">
      <input
        {...props}
        placeholder=" "
        className={cn(
          "floating-input w-full px-3 py-3 text-sm border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-colors",
          error && "border-destructive focus:ring-destructive",
          className,
        )}
      />
      <label className="floating-label">{label}</label>
      {error && <p className="mt-1 text-xs text-destructive">{error}</p>}
    </div>
  )
}
