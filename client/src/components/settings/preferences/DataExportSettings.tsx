"use client"

import { useState } from "react"
import { SettingsCard } from "../SettingsCard"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"
import { settingsApi } from "@/api/settings"
import { Download, Calendar as CalendarIcon, FileText, Database, Mail } from "lucide-react"
import { format } from "date-fns"
import { cn } from "@/lib/utils/utils"

export function DataExportSettings() {
  const [isExporting, setIsExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState<'csv' | 'pdf' | 'json'>('csv')
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({})
  const [autoExport, setAutoExport] = useState(false)
  const [exportFrequency, setExportFrequency] = useState<'daily' | 'weekly' | 'monthly'>('monthly')

  const handleExport = async () => {
    try {
      setIsExporting(true)
      
      const dateRangeParam = dateRange.from && dateRange.to ? {
        from: format(dateRange.from, 'yyyy-MM-dd'),
        to: format(dateRange.to, 'yyyy-MM-dd')
      } : undefined

      const result = await settingsApi.dataExport.exportData(exportFormat, dateRangeParam)
      
      // Open download URL
      window.open(result.downloadUrl, '_blank')
      
    } catch (error) {
      console.error('Export failed:', error)
      // Show error message
    } finally {
      setIsExporting(false)
    }
  }

  const formatOptions = [
    { value: 'csv' as const, label: 'CSV', description: 'Excel-compatible spreadsheet' },
    { value: 'pdf' as const, label: 'PDF', description: 'Formatted report document' },
    { value: 'json' as const, label: 'JSON', description: 'Raw data format' }
  ]

  const frequencyOptions = [
    { value: 'daily' as const, label: 'Daily' },
    { value: 'weekly' as const, label: 'Weekly' },
    { value: 'monthly' as const, label: 'Monthly' }
  ]

  return (
    <SettingsCard
      title="Data Export"
      description="Export your data and configure automatic backups"
    >
      <div className="space-y-6">
        {/* Manual Export */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center space-x-2">
            <Download className="h-4 w-4" />
            <span>Manual Export</span>
          </h4>
          
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="export-format">Export Format</Label>
              <Select value={exportFormat} onValueChange={(value) => setExportFormat(value as 'csv' | 'pdf' | 'json')}>
                <SelectTrigger>
                  <SelectValue placeholder="Select format" />
                </SelectTrigger>
                <SelectContent>
                  {formatOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      <div className="flex items-center space-x-2">
                        <FileText className="h-4 w-4" />
                        <div>
                          <div>{option.label}</div>
                          <div className="text-xs text-muted-foreground">
                            {option.description}
                          </div>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Date Range (Optional)</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !dateRange.from && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {dateRange.from ? (
                      dateRange.to ? (
                        <>
                          {format(dateRange.from, "LLL dd, y")} -{" "}
                          {format(dateRange.to, "LLL dd, y")}
                        </>
                      ) : (
                        format(dateRange.from, "LLL dd, y")
                      )
                    ) : (
                      "All time"
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    initialFocus
                    mode="range"
                    defaultMonth={dateRange.from}
                    selected={{ from: dateRange.from, to: dateRange.to }}
                    onSelect={(range) => setDateRange(range || {})}
                    numberOfMonths={2}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <Button
            onClick={handleExport}
            disabled={isExporting}
            className="w-full sm:w-auto"
          >
            <Download className="h-4 w-4 mr-2" />
            {isExporting ? "Exporting..." : "Export Data"}
          </Button>
        </div>

        {/* Automatic Export */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center space-x-2">
            <Database className="h-4 w-4" />
            <span>Automatic Backup</span>
          </h4>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="auto-export">Enable automatic export</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically export your data on a regular schedule
                </p>
              </div>
              <Switch
                id="auto-export"
                checked={autoExport}
                onCheckedChange={setAutoExport}
              />
            </div>

            {autoExport && (
              <div className="space-y-4 pl-6 border-l-2 border-muted">
                <div className="space-y-2">
                  <Label htmlFor="export-frequency">Frequency</Label>
                  <Select value={exportFrequency} onValueChange={(value) => setExportFrequency(value as 'daily' | 'weekly' | 'monthly')}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="Select frequency" />
                    </SelectTrigger>
                    <SelectContent>
                      {frequencyOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="bg-muted/50 p-3 rounded-md">
                  <p className="text-sm text-muted-foreground flex items-center space-x-1">
                    <Mail className="h-4 w-4" />
                    <span>
                      Automatic exports will be sent to your email address and stored for 30 days.
                    </span>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Export History */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium">Recent Exports</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 border rounded-md">
              <div className="flex items-center space-x-3">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Expenses Report</p>
                  <p className="text-xs text-muted-foreground">
                    CSV • Dec 1, 2024 • 2.3 MB
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="secondary">Completed</Badge>
                <Button variant="ghost" size="sm">
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground">
                Export history will appear here
              </p>
            </div>
          </div>
        </div>
      </div>
    </SettingsCard>
  )
} 