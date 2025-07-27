import { useQuery } from '@tanstack/react-query'
import { settingsApi } from '@/lib/api/settings'
import { Category } from '@/lib/types/settings'

interface UseCategoriesOptions {
  type?: 'income' | 'expense'
  enabled?: boolean
}

export const useCategories = (options: UseCategoriesOptions = {}) => {
  const { type, enabled = true } = options

  return useQuery({
    queryKey: ['categories', type],
    queryFn: async () => {
      const categories = await settingsApi.categories.getCategories()
      return type ? categories.filter(cat => cat.type === type) : categories
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
} 