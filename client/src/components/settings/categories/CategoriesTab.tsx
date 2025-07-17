import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { SettingsCard } from "@/components/settings/SettingsCard"
import { AddCategoryDialog } from "./AddCategoryDialog"
import { Category, CategoryWithChildren } from "@/lib/types/settings"
import { settingsApi } from "@/lib/api/settings"
import { useAuth } from "@/lib/contexts/AuthContext"
import { 
  FolderTree, 
  Edit, 
  Trash2,
  AlertCircle,
  ChevronRight,
  Plus,
  ChevronDown,
} from "lucide-react"
import { Separator } from "@/components/ui/separator"

function SubcategoryItem({ category, onRefresh }: { 
  category: CategoryWithChildren, 
  onRefresh: () => void
}) {
  const createdAt = category.createdAt ? new Date(category.createdAt) : null
  const isValidDate = createdAt && !isNaN(createdAt.getTime())

  return (
    <div className="relative">
      <div className="absolute left-2 top-0 bottom-0 w-px bg-border" />
      <div className="flex items-center justify-between py-3 px-4 hover:bg-muted/50 rounded-md ml-6">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <FolderTree className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">{category.name}</span>
            <Badge variant={category.type === 'expense' ? 'destructive' : 'default'} className="text-xs">
              Subcategory
            </Badge>
          </div>
          {isValidDate && (
            <span className="text-sm text-muted-foreground">
              {createdAt.toLocaleDateString(undefined, { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="sm">
            <Edit className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

function CategoryCard({ category, onRefresh }: { 
  category: CategoryWithChildren, 
  onRefresh: () => void
}) {
  const [isExpanded, setIsExpanded] = useState(true)
  const createdAt = category.createdAt ? new Date(category.createdAt) : null
  const isValidDate = createdAt && !isNaN(createdAt.getTime())
  const hasSubcategories = category.children && category.children.length > 0

  return (
    <div className={`border rounded-lg p-4 space-y-4 ${hasSubcategories ? 'bg-card' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-white"
            style={{ backgroundColor: category.color || '#10B981' }}
          >
            <FolderTree className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-medium">{category.name}</span>
              <Badge variant={category.type === 'expense' ? 'destructive' : 'default'}>
                {category.type}
              </Badge>
              {hasSubcategories && (
                <Badge variant="outline" className="text-xs">
                  {category.children.length} subcategories
                </Badge>
              )}
              {hasSubcategories && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="p-0 h-auto"
                  onClick={() => setIsExpanded(!isExpanded)}
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              )}
            </div>
            {isValidDate && (
              <p className="text-sm text-muted-foreground">
                Created {createdAt.toLocaleDateString(undefined, { 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <AddCategoryDialog 
            onSuccess={onRefresh}
            parentId={category.id}
            trigger={
              <Button variant="outline" size="sm" className="flex items-center space-x-1">
                <Plus className="h-4 w-4" />
                <span>Add Subcategory</span>
              </Button>
            }
          />
          <Button variant="ghost" size="sm">
            <Edit className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {hasSubcategories && isExpanded && (
        <>
          <Separator />
          <div className="space-y-1 relative">
            <div className="flex items-center space-x-2 mb-2 pl-4">
              <div className="w-1 h-4 bg-muted-foreground/20 rounded" />
              <span className="text-sm text-muted-foreground">Subcategories</span>
            </div>
            <div className="space-y-1">
              {category.children.map((subcategory) => (
                <SubcategoryItem 
                  key={subcategory.id} 
                  category={subcategory}
                  onRefresh={onRefresh}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function CategoryList({ 
  categories, 
  type, 
  onRefresh 
}: { 
  categories: CategoryWithChildren[], 
  type: 'expense' | 'income',
  onRefresh: () => void
}) {
  // Only show root categories (no parent)
  const rootCategories = categories.filter(cat => cat.type === type && !cat.parentId)

  if (rootCategories.length === 0) {
    return (
      <div className="text-center py-6 border-2 border-dashed border-muted rounded-lg">
        <FolderTree className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <p className="text-muted-foreground mb-2">No {type} categories</p>
        <p className="text-sm text-muted-foreground mb-4">
          Create your first {type} category to start organizing
        </p>
        <AddCategoryDialog onSuccess={onRefresh} />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {rootCategories.map((category) => (
        <CategoryCard 
          key={category.id} 
          category={category}
          onRefresh={onRefresh}
        />
      ))}
    </div>
  )
}

export function CategoriesTab() {
  const [categories, setCategories] = useState<CategoryWithChildren[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { token } = useAuth()

  const fetchCategories = async () => {
    if (!token) {
      setError('Please sign in to view categories')
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)
      const data = await settingsApi.categories.getCategoriesHierarchy()
      // Sort categories by name within their type
      const sortedData = data.sort((a, b) => a.name.localeCompare(b.name))
      setCategories(sortedData)
    } catch (error) {
      console.error('Failed to fetch categories:', error)
      setError('Failed to load categories. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchCategories()
  }, [token])

  if (error) {
    return (
      <div className="space-y-6">
        <SettingsCard
          title="Categories"
          description="Organize your expenses and income with custom categories"
        >
          <div className="flex items-center justify-center p-6 text-destructive space-x-2">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
        </SettingsCard>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <SettingsCard
        title="Categories"
        description="Organize your expenses and income with custom categories"
        headerAction={
          <AddCategoryDialog onSuccess={fetchCategories} />
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-4">Expense Categories</h3>
            <CategoryList 
              categories={categories} 
              type="expense" 
              onRefresh={fetchCategories}
            />
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4">Income Categories</h3>
            <CategoryList 
              categories={categories} 
              type="income" 
              onRefresh={fetchCategories}
            />
          </div>
        </div>
      </SettingsCard>
    </div>
  )
} 