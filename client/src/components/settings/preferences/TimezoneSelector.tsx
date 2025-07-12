"use client"

import { useState, useMemo } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Check, ChevronsUpDown } from "lucide-react"
import { cn } from "@/lib/utils/utils"

interface TimezoneOption {
  value: string
  label: string
  offset: string
  region: string
}

const timezones: TimezoneOption[] = [
  // North America
  { value: "America/New_York", label: "New York", offset: "UTC-5/-4", region: "North America" },
  { value: "America/Chicago", label: "Chicago", offset: "UTC-6/-5", region: "North America" },
  { value: "America/Denver", label: "Denver", offset: "UTC-7/-6", region: "North America" },
  { value: "America/Los_Angeles", label: "Los Angeles", offset: "UTC-8/-7", region: "North America" },
  { value: "America/Phoenix", label: "Phoenix", offset: "UTC-7", region: "North America" },
  { value: "America/Toronto", label: "Toronto", offset: "UTC-5/-4", region: "North America" },
  { value: "America/Vancouver", label: "Vancouver", offset: "UTC-8/-7", region: "North America" },
  { value: "America/Mexico_City", label: "Mexico City", offset: "UTC-6/-5", region: "North America" },

  // Europe
  { value: "Europe/London", label: "London", offset: "UTC+0/+1", region: "Europe" },
  { value: "Europe/Paris", label: "Paris", offset: "UTC+1/+2", region: "Europe" },
  { value: "Europe/Berlin", label: "Berlin", offset: "UTC+1/+2", region: "Europe" },
  { value: "Europe/Rome", label: "Rome", offset: "UTC+1/+2", region: "Europe" },
  { value: "Europe/Madrid", label: "Madrid", offset: "UTC+1/+2", region: "Europe" },
  { value: "Europe/Amsterdam", label: "Amsterdam", offset: "UTC+1/+2", region: "Europe" },
  { value: "Europe/Stockholm", label: "Stockholm", offset: "UTC+1/+2", region: "Europe" },
  { value: "Europe/Zurich", label: "Zurich", offset: "UTC+1/+2", region: "Europe" },
  { value: "Europe/Moscow", label: "Moscow", offset: "UTC+3", region: "Europe" },

  // Asia
  { value: "Asia/Tokyo", label: "Tokyo", offset: "UTC+9", region: "Asia" },
  { value: "Asia/Shanghai", label: "Shanghai", offset: "UTC+8", region: "Asia" },
  { value: "Asia/Hong_Kong", label: "Hong Kong", offset: "UTC+8", region: "Asia" },
  { value: "Asia/Singapore", label: "Singapore", offset: "UTC+8", region: "Asia" },
  { value: "Asia/Seoul", label: "Seoul", offset: "UTC+9", region: "Asia" },
  { value: "Asia/Bangkok", label: "Bangkok", offset: "UTC+7", region: "Asia" },
  { value: "Asia/Mumbai", label: "Mumbai", offset: "UTC+5:30", region: "Asia" },
  { value: "Asia/Dubai", label: "Dubai", offset: "UTC+4", region: "Asia" },

  // Australia & Oceania
  { value: "Australia/Sydney", label: "Sydney", offset: "UTC+10/+11", region: "Australia" },
  { value: "Australia/Melbourne", label: "Melbourne", offset: "UTC+10/+11", region: "Australia" },
  { value: "Australia/Perth", label: "Perth", offset: "UTC+8", region: "Australia" },
  { value: "Pacific/Auckland", label: "Auckland", offset: "UTC+12/+13", region: "Pacific" },

  // South America
  { value: "America/Sao_Paulo", label: "São Paulo", offset: "UTC-3", region: "South America" },
  { value: "America/Buenos_Aires", label: "Buenos Aires", offset: "UTC-3", region: "South America" },
  { value: "America/Lima", label: "Lima", offset: "UTC-5", region: "South America" },

  // Africa
  { value: "Africa/Lagos", label: "Lagos", offset: "UTC+1", region: "Africa" },
  { value: "Africa/Cairo", label: "Cairo", offset: "UTC+2", region: "Africa" },
  { value: "Africa/Johannesburg", label: "Johannesburg", offset: "UTC+2", region: "Africa" },

  // UTC
  { value: "UTC", label: "UTC", offset: "UTC+0", region: "UTC" },
]

interface TimezoneSelectorProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function TimezoneSelector({ value, onChange, disabled }: TimezoneSelectorProps) {
  const [open, setOpen] = useState(false)
  const [searchValue, setSearchValue] = useState("")

  const filteredTimezones = useMemo(() => {
    if (!searchValue) return timezones

    return timezones.filter((timezone) =>
      timezone.label.toLowerCase().includes(searchValue.toLowerCase()) ||
      timezone.region.toLowerCase().includes(searchValue.toLowerCase()) ||
      timezone.value.toLowerCase().includes(searchValue.toLowerCase())
    )
  }, [searchValue])

  const groupedTimezones = useMemo(() => {
    const groups: Record<string, TimezoneOption[]> = {}
    
    filteredTimezones.forEach((timezone) => {
      if (!groups[timezone.region]) {
        groups[timezone.region] = []
      }
      groups[timezone.region].push(timezone)
    })

    return groups
  }, [filteredTimezones])

  const selectedTimezone = timezones.find((tz) => tz.value === value)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
          disabled={disabled}
        >
          {selectedTimezone ? (
            <div className="flex items-center space-x-2">
              <span>{selectedTimezone.label}</span>
              <span className="text-muted-foreground text-sm">
                ({selectedTimezone.offset})
              </span>
            </div>
          ) : (
            "Select timezone..."
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0">
        <Command>
          <CommandInput
            placeholder="Search timezone..."
            value={searchValue}
            onValueChange={setSearchValue}
          />
          <CommandEmpty>No timezone found.</CommandEmpty>
          <ScrollArea className="h-72">
            {Object.entries(groupedTimezones).map(([region, timezones]) => (
              <CommandGroup key={region} heading={region}>
                {timezones.map((timezone) => (
                  <CommandItem
                    key={timezone.value}
                    value={timezone.value}
                    onSelect={(currentValue) => {
                      onChange(currentValue)
                      setOpen(false)
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value === timezone.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="flex items-center justify-between w-full">
                      <span>{timezone.label}</span>
                      <span className="text-muted-foreground text-sm">
                        {timezone.offset}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </ScrollArea>
        </Command>
      </PopoverContent>
    </Popover>
  )
} 