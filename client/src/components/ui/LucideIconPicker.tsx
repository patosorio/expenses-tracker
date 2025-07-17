"use client"

import { useState } from 'react'
import { Popover, PopoverContent, PopoverTrigger } from './popover'
import { Button } from './button'
import { ScrollArea } from './scroll-area'
import { Input } from './input'
import { Search } from 'lucide-react'
import { FolderTree, DollarSign, CreditCard, Wallet, ShoppingCart, Coffee, Car, Home, Heart, Gift, Music, Film, Book, Briefcase, Activity, Utensils } from 'lucide-react'

const iconList = [
  { name: 'FolderTree', icon: FolderTree },
  { name: 'DollarSign', icon: DollarSign },
  { name: 'CreditCard', icon: CreditCard },
  { name: 'Wallet', icon: Wallet },
  { name: 'ShoppingCart', icon: ShoppingCart },
  { name: 'Coffee', icon: Coffee },
  { name: 'Car', icon: Car },
  { name: 'Home', icon: Home },
  { name: 'Heart', icon: Heart },
  { name: 'Gift', icon: Gift },
  { name: 'Music', icon: Music },
  { name: 'Film', icon: Film },
  { name: 'Book', icon: Book },
  { name: 'Briefcase', icon: Briefcase },
  { name: 'Activity', icon: Activity },
  { name: 'Utensils', icon: Utensils },
]

interface LucideIconPickerProps {
  value?: string;
  onChange: (value: string) => void;
}

export function LucideIconPicker({ value, onChange }: LucideIconPickerProps) {
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)

  const filteredIcons = iconList.filter(icon => 
    icon.name.toLowerCase().includes(search.toLowerCase())
  )

  const selectedIcon = iconList.find(i => i.name === value)
  const SelectedIcon = selectedIcon?.icon

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button 
          variant="outline" 
          className="w-full justify-start gap-2"
        >
          {SelectedIcon ? (
            <>
              <SelectedIcon className="h-4 w-4" />
              <span>{value}</span>
            </>
          ) : (
            'Select icon'
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" style={{ zIndex: 9999 }}>
        <div className="p-2 border-b">
          <div className="flex items-center gap-2 px-2 py-1">
            <Search className="w-4 h-4 opacity-50" />
            <Input
              placeholder="Search icons..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
            />
          </div>
        </div>
        <ScrollArea className="h-72">
          <div className="grid grid-cols-4 gap-2 p-2">
            {filteredIcons.map(({ name, icon: Icon }) => (
              <Button
                key={name}
                variant="ghost"
                className="flex flex-col items-center gap-1 p-2 h-auto"
                onClick={() => {
                  onChange(name)
                  setOpen(false)
                }}
              >
                <Icon className="w-5 h-5" />
                <span className="text-xs">{name}</span>
              </Button>
            ))}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  )
} 