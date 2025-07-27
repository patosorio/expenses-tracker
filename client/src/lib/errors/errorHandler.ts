import { toast } from '@/components/ui/use-toast'

export interface ApiErrorResponse {
  detail: string
  code?: string
  message?: string
  status?: number
  context?: Record<string, unknown>
}

export interface ErrorHandlerOptions {
  showToast?: boolean
  fallbackMessage?: string
  action?: string
}

export class AppError extends Error {
  constructor(
    message: string,
    public code?: string,
    public status?: number,
    public context?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'AppError'
  }
}

/**
 * Maps backend HTTP status codes to user-friendly messages
 */
const getErrorMessageByStatus = (status: number, action?: string): string => {
  const actionContext = action ? ` ${action}` : ''
  
  switch (status) {
    case 400:
      return `Invalid request data${actionContext}. Please check your input and try again.`
    case 401:
      return 'You are not authorized to perform this action. Please sign in again.'
    case 403:
      return `You don't have permission to${actionContext}. Contact your administrator if needed.`
    case 404:
      return `The requested resource was not found${actionContext}.`
    case 409:
      return `A conflict occurred${actionContext}. This data may already exist or be in use.`
    case 422:
      return `Validation failed${actionContext}. Please check the required fields.`
    case 429:
      return 'Too many requests. Please wait a moment and try again.'
    case 500:
    case 502:
    case 503:
    case 504:
      return `Server error occurred${actionContext}. Please try again later.`
    default:
      return `An unexpected error occurred${actionContext}. Please try again.`
  }
}

/**
 * Extracts error information from various error types
 */
const extractErrorInfo = (error: unknown): ApiErrorResponse => {
  // Handle AppError (our custom error type)
  if (error instanceof AppError) {
    return {
      detail: error.message,
      code: error.code,
      status: error.status,
      context: error.context
    }
  }

  // Handle Response errors (fetch API)
  if (error && typeof error === 'object' && 'status' in error && 'data' in error) {
    const responseError = error as { status: number; data?: any }
    return {
      detail: responseError.data?.detail || responseError.data?.message || 'Request failed',
      code: responseError.data?.code,
      status: responseError.status,
      context: responseError.data?.context
    }
  }

  // Handle standard Error objects
  if (error instanceof Error) {
    return {
      detail: error.message,
      status: 500
    }
  }

  // Handle string errors
  if (typeof error === 'string') {
    return {
      detail: error,
      status: 500
    }
  }

  // Fallback for unknown error types
  return {
    detail: 'An unknown error occurred',
    status: 500
  }
}

/**
 * Central error handler for the application
 */
export const handleError = (
  error: unknown, 
  options: ErrorHandlerOptions = {}
): AppError => {
  const {
    showToast = true,
    fallbackMessage = 'An unexpected error occurred',
    action
  } = options

  const errorInfo = extractErrorInfo(error)
  
  // Use backend error message if available, otherwise use status-based message
  const userMessage = errorInfo.detail || 
    (errorInfo.status ? getErrorMessageByStatus(errorInfo.status, action) : fallbackMessage)

  // Show toast notification if requested
  if (showToast) {
    toast({
      title: 'Error',
      description: userMessage,
      variant: 'destructive',
    })
  }

  // Log error for debugging (only in development)
  if (process.env.NODE_ENV === 'development') {
    console.error('Error handled:', {
      originalError: error,
      errorInfo,
      userMessage,
      context: errorInfo.context
    })
  }

  // Return normalized error
  return new AppError(
    userMessage,
    errorInfo.code,
    errorInfo.status,
    errorInfo.context
  )
}

/**
 * Specialized error handlers for different operations
 */
export const errorHandlers = {
  expenses: {
    create: (error: unknown) => handleError(error, { 
      action: 'creating expense',
      fallbackMessage: 'Failed to create expense. Please check your data and try again.'
    }),
    
    update: (error: unknown) => handleError(error, { 
      action: 'updating expense',
      fallbackMessage: 'Failed to update expense. Please try again.'
    }),
    
    delete: (error: unknown) => handleError(error, { 
      action: 'deleting expense',
      fallbackMessage: 'Failed to delete expense. Please try again.'
    }),
    
    fetch: (error: unknown) => handleError(error, { 
      action: 'loading expenses',
      fallbackMessage: 'Failed to load expenses. Please refresh the page.'
    }),

    markPaid: (error: unknown) => handleError(error, {
      action: 'marking expense as paid',
      fallbackMessage: 'Failed to mark expense as paid. Please try again.'
    })
  },

  auth: {
    login: (error: unknown) => handleError(error, {
      action: 'signing in',
      fallbackMessage: 'Failed to sign in. Please check your credentials.'
    }),
    
    logout: (error: unknown) => handleError(error, {
      action: 'signing out',
      fallbackMessage: 'Failed to sign out. Please try again.'
    })
  },

  validation: {
    required: (field: string) => handleError(
      `${field} is required`,
      { showToast: true, fallbackMessage: 'Please fill in all required fields.' }
    ),
    
    invalid: (field: string, reason?: string) => handleError(
      `${field} is invalid${reason ? `: ${reason}` : ''}`,
      { showToast: true, fallbackMessage: 'Please check your input and try again.' }
    )
  }
}