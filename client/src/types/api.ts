// API Error types
export interface ApiErrorResponse {
  detail: string;
  code?: string;
  message?: string;
  [key: string]: unknown;
}

export interface ApiSuccessResponse<T = unknown> {
  data: T;
  message?: string;
  [key: string]: unknown;
}

// Request/Response types
export interface PaginationParams {
  page?: number;
  limit?: number;
  per_page?: number;
}

export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface SearchParams {
  search?: string;
}

// Common API response patterns
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
}

// API Hook types
export interface UseApiOptions {
  enabled?: boolean;
  refetchOnWindowFocus?: boolean;
  refetchOnReconnect?: boolean;
  retryOnError?: boolean;
  retryCount?: number;
}

export interface UseApiReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  mutate: (data: T) => void;
}

// Request configuration
export interface RequestConfig {
  retries?: number;
  retryDelay?: number;
  timeout?: number;
  headers?: Record<string, string>;
}

// API Client configuration
export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  headers?: Record<string, string>;
} 