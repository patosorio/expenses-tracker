"use client"

import { useState, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "@/components/ui/command"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils/utils"
import { 
  Search,
  X,
  // Business & Finance
  Building2,
  CreditCard,
  DollarSign,
  TrendingUp,
  TrendingDown,
  PiggyBank,
  Receipt,
  Wallet,
  Banknote,
  Calculator,
  FileText,
  BarChart3,
  PieChart,
  // General
  Home,
  Car,
  Plane,
  Coffee,
  ShoppingCart,
  Gift,
  Heart,
  Star,
  Settings,
  User,
  Users,
  Calendar,
  Clock,
  MapPin,
  Phone,
  Mail,
  Lock,
  Key,
  Shield,
  // Categories
  Utensils,
  ShoppingBag,
  Gamepad2,
  Book,
  Music,
  Camera,
  Smartphone,
  Laptop,
  Monitor,
  Headphones,
  // Transportation
  Fuel,
  Bus,
  Train,
  Bike,
  // Health & Fitness
  Dumbbell,
  Activity,
  Pill,
  // Utilities
  Zap,
  Wifi,
  Thermometer,
  // Entertainment
  Film,
  Tv,
  // Work
  Briefcase,
  FileCheck,
  Presentation,
  // Food
  ChefHat,
  Pizza,
  // Other common icons
  Tag,
  Bookmark,
  Flag,
  Bell,
  Archive,
  Trash2,
  Edit,
  Plus,
  Minus,
  Check,
  AlertCircle,
  Info,
  HelpCircle
} from "lucide-react"

interface IconOption {
  name: string
  icon: React.ComponentType<any>
  category: string
  keywords: string[]
}

const iconOptions: IconOption[] = [
  // Business & Finance
  { name: "building-2", icon: Building2, category: "Business", keywords: ["company", "office", "work"] },
  { name: "credit-card", icon: CreditCard, category: "Finance", keywords: ["payment", "money", "card"] },
  { name: "dollar-sign", icon: DollarSign, category: "Finance", keywords: ["money", "currency", "cash"] },
  { name: "trending-up", icon: TrendingUp, category: "Finance", keywords: ["growth", "profit", "increase"] },
  { name: "trending-down", icon: TrendingDown, category: "Finance", keywords: ["loss", "decrease", "decline"] },
  { name: "piggy-bank", icon: PiggyBank, category: "Finance", keywords: ["savings", "money", "investment"] },
  { name: "receipt", icon: Receipt, category: "Finance", keywords: ["expense", "bill", "invoice"] },
  { name: "wallet", icon: Wallet, category: "Finance", keywords: ["money", "cash", "payment"] },
  { name: "banknote", icon: Banknote, category: "Finance", keywords: ["money", "cash", "currency"] },
  { name: "calculator", icon: Calculator, category: "Finance", keywords: ["math", "calculation", "accounting"] },
  { name: "file-text", icon: FileText, category: "Business", keywords: ["document", "report", "invoice"] },
  { name: "bar-chart-3", icon: BarChart3, category: "Finance", keywords: ["analytics", "data", "graph"] },
  { name: "pie-chart", icon: PieChart, category: "Finance", keywords: ["analytics", "data", "stats"] },

  // General
  { name: "home", icon: Home, category: "General", keywords: ["house", "residence", "property"] },
  { name: "car", icon: Car, category: "Transportation", keywords: ["vehicle", "auto", "drive"] },
  { name: "plane", icon: Plane, category: "Transportation", keywords: ["travel", "flight", "trip"] },
  { name: "coffee", icon: Coffee, category: "Food & Drink", keywords: ["beverage", "drink", "cafe"] },
  { name: "shopping-cart", icon: ShoppingCart, category: "Shopping", keywords: ["purchase", "buy", "store"] },
  { name: "gift", icon: Gift, category: "General", keywords: ["present", "celebration", "birthday"] },
  { name: "heart", icon: Heart, category: "General", keywords: ["love", "favorite", "like"] },
  { name: "star", icon: Star, category: "General", keywords: ["favorite", "rating", "quality"] },
  { name: "settings", icon: Settings, category: "General", keywords: ["config", "preferences", "options"] },
  { name: "user", icon: User, category: "General", keywords: ["person", "profile", "account"] },
  { name: "users", icon: Users, category: "General", keywords: ["people", "team", "group"] },
  { name: "calendar", icon: Calendar, category: "General", keywords: ["date", "schedule", "appointment"] },
  { name: "clock", icon: Clock, category: "General", keywords: ["time", "schedule", "timing"] },
  { name: "map-pin", icon: MapPin, category: "General", keywords: ["location", "address", "place"] },

  // Technology
  { name: "smartphone", icon: Smartphone, category: "Technology", keywords: ["phone", "mobile", "device"] },
  { name: "laptop", icon: Laptop, category: "Technology", keywords: ["computer", "device", "work"] },
  { name: "monitor", icon: Monitor, category: "Technology", keywords: ["screen", "computer", "display"] },
  { name: "headphones", icon: Headphones, category: "Technology", keywords: ["audio", "music", "sound"] },
  { name: "wifi", icon: Wifi, category: "Technology", keywords: ["internet", "connection", "network"] },

  // Food & Dining
  { name: "utensils", icon: Utensils, category: "Food & Drink", keywords: ["dining", "restaurant", "meal"] },
  { name: "chef-hat", icon: ChefHat, category: "Food & Drink", keywords: ["cooking", "restaurant", "food"] },
  { name: "pizza", icon: Pizza, category: "Food & Drink", keywords: ["food", "meal", "dining"] },

  // Transportation
  { name: "fuel", icon: Fuel, category: "Transportation", keywords: ["gas", "petrol", "energy"] },
  { name: "bus", icon: Bus, category: "Transportation", keywords: ["public", "transport", "travel"] },
  { name: "train", icon: Train, category: "Transportation", keywords: ["railway", "transport", "travel"] },
  { name: "bike", icon: Bike, category: "Transportation", keywords: ["bicycle", "cycling", "exercise"] },

  // Health & Fitness
  { name: "dumbbell", icon: Dumbbell, category: "Health & Fitness", keywords: ["exercise", "gym", "workout"] },
  { name: "activity", icon: Activity, category: "Health & Fitness", keywords: ["health", "fitness", "exercise"] },
  { name: "pill", icon: Pill, category: "Health & Fitness", keywords: ["medicine", "health", "medical"] },

  // Entertainment
  { name: "film", icon: Film, category: "Entertainment", keywords: ["movie", "cinema", "video"] },
  { name: "tv", icon: Tv, category: "Entertainment", keywords: ["television", "media", "screen"] },
  { name: "music", icon: Music, category: "Entertainment", keywords: ["audio", "song", "sound"] },
  { name: "gamepad-2", icon: Gamepad2, category: "Entertainment", keywords: ["gaming", "play", "controller"] },
  { name: "book", icon: Book, category: "Entertainment", keywords: ["reading", "education", "library"] },
  { name: "camera", icon: Camera, category: "Entertainment", keywords: ["photo", "picture", "photography"] },

  // Utilities
  { name: "zap", icon: Zap, category: "Utilities", keywords: ["electricity", "power", "energy"] },
  { name: "thermometer", icon: Thermometer, category: "Utilities", keywords: ["temperature", "heating", "cooling"] },

  // Work & Business
  { name: "briefcase", icon: Briefcase, category: "Business", keywords: ["work", "job", "professional"] },
  { name: "file-check", icon: FileCheck, category: "Business", keywords: ["document", "completed", "verified"] },
  { name: "presentation", icon: Presentation, category: "Business", keywords: ["meeting", "presentation", "work"] },

  // Common Actions
  { name: "tag", icon: Tag, category: "General", keywords: ["label", "category", "organize"] },
  { name: "bookmark", icon: Bookmark, category: "General", keywords: ["save", "favorite", "mark"] },
  { name: "flag", icon: Flag, category: "General", keywords: ["important", "priority", "mark"] },
  { name: "bell", icon: Bell, category: "General", keywords: ["notification", "alert", "reminder"] },
  { name: "archive", icon: Archive, category: "General", keywords: ["storage", "organize", "file"] },
  { name: "trash-2", icon: Trash2, category: "General", keywords: ["delete", "remove", "discard"] },
  { name: "edit", icon: Edit, category: "General", keywords: ["modify", "change", "update"] },
  { name: "plus", icon: Plus, category: "General", keywords: ["add", "create", "new"] },
  { name: "minus", icon: Minus, category: "General", keywords: ["remove", "subtract", "delete"] },
  { name: "check", icon: Check, category: "General", keywords: ["complete", "done", "success"] },
  { name: "alert-circle", icon: AlertCircle, category: "General", keywords: ["warning", "attention", "important"] },
  { name: "info", icon: Info, category: "General", keywords: ["information", "details", "help"] },
  { name: "help-circle", icon: HelpCircle, category: "General", keywords: ["question", "support", "help"] },
]

interface LucideIconPickerProps {
  value?: string
  onChange: (iconName: string) => void
  placeholder?: string
  disabled?: boolean
}

export function LucideIconPicker({ 
  value, 
  onChange, 
  placeholder = "Select an icon",
  disabled = false 
}: LucideIconPickerProps) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string>("All")

  const categories = useMemo(() => {
    const cats = Array.from(new Set(iconOptions.map(icon => icon.category)))
    return ["All", ...cats.sort()]
  }, [])

  const filteredIcons = useMemo(() => {
    return iconOptions.filter(icon => {
      const matchesSearch = searchQuery === "" || 
        icon.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        icon.keywords.some(keyword => keyword.toLowerCase().includes(searchQuery.toLowerCase()))
      
      const matchesCategory = selectedCategory === "All" || icon.category === selectedCategory
      
      return matchesSearch && matchesCategory
    })
  }, [searchQuery, selectedCategory])

  const selectedIcon = iconOptions.find(icon => icon.name === value)
  const SelectedIconComponent = selectedIcon?.icon

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
          <div className="flex items-center space-x-2">
            {SelectedIconComponent ? (
              <>
                <SelectedIconComponent className="h-4 w-4" />
                <span>{selectedIcon?.name}</span>
              </>
            ) : (
              <span className="text-muted-foreground">{placeholder}</span>
            )}
          </div>
          <Search className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="start">
        <Command>
          <div className="p-3 border-b">
            <CommandInput
              placeholder="Search icons..."
              value={searchQuery}
              onValueChange={setSearchQuery}
            />
          </div>
          
          <div className="p-3 border-b">
            <div className="flex flex-wrap gap-1">
              {categories.map((category) => (
                <Badge
                  key={category}
                  variant={selectedCategory === category ? "default" : "secondary"}
                  className="cursor-pointer text-xs"
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </Badge>
              ))}
            </div>
          </div>

          <ScrollArea className="h-60">
            <div className="p-3">
              {filteredIcons.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground">
                  No icons found
                </div>
              ) : (
                <div className="grid grid-cols-6 gap-2">
                  {filteredIcons.map((icon) => {
                    const IconComponent = icon.icon
                    const isSelected = value === icon.name
                    
                    return (
                      <Button
                        key={icon.name}
                        variant={isSelected ? "default" : "ghost"}
                        size="sm"
                        className={cn(
                          "h-10 w-10 p-0 flex items-center justify-center",
                          isSelected && "ring-2 ring-offset-2 ring-ring"
                        )}
                        onClick={() => {
                          onChange(icon.name)
                          setOpen(false)
                        }}
                        title={icon.name}
                      >
                        <IconComponent className="h-4 w-4" />
                      </Button>
                    )
                  })}
                </div>
              )}
            </div>
          </ScrollArea>
          
          {value && (
            <div className="p-3 border-t">
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => {
                  onChange("")
                  setOpen(false)
                }}
              >
                <X className="h-4 w-4 mr-2" />
                Clear selection
              </Button>
            </div>
          )}
        </Command>
      </PopoverContent>
    </Popover>
  )
}

// Utility component to render an icon by name
export function LucideIcon({ 
  name, 
  className,
  ...props 
}: { 
  name: string
  className?: string
} & React.ComponentPropsWithoutRef<"svg">) {
  const iconOption = iconOptions.find(icon => icon.name === name)
  
  if (!iconOption) {
    return <div className={cn("h-4 w-4 bg-muted rounded", className)} />
  }
  
  const IconComponent = iconOption.icon
  return <IconComponent className={className} {...props} />
}

// Export the icon options for use in other components
export { iconOptions } 