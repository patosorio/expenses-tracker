import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { AuthProvider } from "@/lib/contexts/AuthContext"
import { ApiProvider } from "@/lib/contexts/ApiContext"
import { Toaster } from "@/components/ui/toaster"
import { QueryProvider } from "@/lib/contexts/QueryProvider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "ExpenseTracker - Household Expense Management",
  description: "Track and manage your household expenses with ease",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <ApiProvider>
          <QueryProvider>  {/* Add this */}
            {children}
          </QueryProvider>
          </ApiProvider>
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  )
}
