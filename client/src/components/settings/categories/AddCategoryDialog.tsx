import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { LucideIconPicker } from "@/components/ui/LucideIconPicker"
import { CategoryFormData, Category } from "@/lib/types/settings"
import { settingsApi } from "@/lib/api/settings"
import { Plus } from 'lucide-react'

interface AddCategoryDialogProps {
  onSuccess: () => void;
  trigger?: React.ReactNode;
  parentId?: string;
}

export function AddCategoryDialog({ onSuccess, trigger, parentId }: AddCategoryDialogProps) {
  const [open, setOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])
  const [isSubcategory, setIsSubcategory] = useState(!!parentId)
  const [selectedParentCategory, setSelectedParentCategory] = useState<Category | null>(null)

  const [formData, setFormData] = useState<CategoryFormData>({
    name: '',
    type: 'expense',
    color: '#10B981',
    icon: 'FolderTree',
    isDefault: false,
    parentId: parentId || undefined
  })

  // Reset form data when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setFormData({
        name: '',
        type: 'expense',
        color: '#10B981',
        icon: 'FolderTree',
        isDefault: false,
        parentId: parentId || undefined
      })
      setIsSubcategory(!!parentId)
      setSelectedParentCategory(null)
    }
  }, [open, parentId])

  // Fetch existing categories for parent selection
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await settingsApi.categories.getCategories()
        setCategories(data)
        
        // If parentId is provided, find and set the parent category
        if (parentId) {
          const parent = data.find(cat => cat.id === parentId)
          if (parent) {
            setSelectedParentCategory(parent)
            setFormData(prev => ({
              ...prev,
              type: parent.type, // Set initial type to match parent
              parentId
            }))
          }
        }
      } catch (error) {
        console.error('Failed to fetch categories:', error)
      }
    }
    if (open) {
      fetchCategories()
    }
  }, [open, parentId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setIsLoading(true)
      await settingsApi.categories.createCategory(formData)
      setOpen(false)
      onSuccess()
    } catch (error) {
      console.error('Failed to create category:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleTypeChange = (value: string) => {
    if (value !== 'expense' && value !== 'income') return
    
    // If this is a subcategory creation (parentId provided), don't allow type change
    if (parentId) {
      return
    }

    setFormData({ 
      ...formData, 
      type: value,
      // Only clear parentId if not adding a subcategory directly
      parentId: parentId || undefined
    })
  }

  // Filter out categories that would create circular references
  const availableParentCategories = categories.filter(category => {
    // Don't allow a category to be its own parent
    if (category.id === formData.parentId) return false
    
    // When adding a subcategory directly (parentId provided), don't filter by type
    // When creating a new subcategory with switch, filter by type
    if (!parentId && category.type !== formData.type) return false

    // Don't allow deep nesting (e.g., limit to 3 levels)
    if (category.level >= 2) return false

    return true
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button size="sm" className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Add Category</span>
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {parentId ? `Add Subcategory to ${selectedParentCategory?.name || ''}` : 'Add Category'}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="name" className="text-sm font-medium">Name</label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Category name"
              required
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="type" className="text-sm font-medium">Type</label>
            <Select
              value={formData.type}
              onValueChange={handleTypeChange}
              disabled={!!parentId} // Disable type selection when adding subcategory
            >
              <SelectTrigger className="w-full">
                <SelectValue>
                  {formData.type === 'expense' ? 'Expense' : 'Income'}
                </SelectValue>
              </SelectTrigger>
              <SelectContent className="z-[150]">
                <SelectItem value="expense">Expense</SelectItem>
                <SelectItem value="income">Income</SelectItem>
              </SelectContent>
            </Select>
            {parentId && (
              <p className="text-sm text-muted-foreground">
                Subcategories must be of the same type as their parent
              </p>
            )}
          </div>

          {!parentId && (
            <div className="flex items-center justify-between space-x-2">
              <label htmlFor="isSubcategory" className="text-sm font-medium">
                Create as subcategory
              </label>
              <Switch
                id="isSubcategory"
                checked={isSubcategory}
                onCheckedChange={(checked) => {
                  setIsSubcategory(checked)
                  if (!checked) {
                    setFormData(prev => ({ ...prev, parentId: undefined }))
                  }
                }}
              />
            </div>
          )}

          {(isSubcategory || parentId) && availableParentCategories.length > 0 && (
            <div className="space-y-2">
              <label htmlFor="parentId" className="text-sm font-medium">Parent Category</label>
              <Select
                value={formData.parentId || "none"}
                onValueChange={(value) => setFormData({ ...formData, parentId: value === "none" ? undefined : value })}
                disabled={!!parentId} // Disable parent selection when adding subcategory directly
              >
                <SelectTrigger className="w-full">
                  <SelectValue>
                    {formData.parentId 
                      ? categories.find(c => c.id === formData.parentId)?.name || 'Select parent category'
                      : 'None (Root Category)'
                    }
                  </SelectValue>
                </SelectTrigger>
                <SelectContent className="z-[150]">
                  {!parentId && <SelectItem value="none">None (Root Category)</SelectItem>}
                  {availableParentCategories.map((category) => (
                    <SelectItem key={category.id} value={category.id}>
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <label htmlFor="icon" className="text-sm font-medium">Icon</label>
            <LucideIconPicker
              value={formData.icon}
              onChange={(icon) => setFormData({ ...formData, icon })}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="color" className="text-sm font-medium">Color</label>
            <Input
              id="color"
              type="color"
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              className="h-10 px-2"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Category'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
} 