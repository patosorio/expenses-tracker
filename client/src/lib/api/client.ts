import { getAuth } from 'firebase/auth';
import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// Error types for better error handling
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthError';
  }
}

// Request configuration
export interface RequestConfig extends AxiosRequestConfig {
  retries?: number;
  retryDelay?: number;
  timeout?: number;
}

// Response wrapper
export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

// Interceptor types
export type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
export type ResponseInterceptor = (response: AxiosResponse) => AxiosResponse | Promise<AxiosResponse>;
export type ErrorInterceptor = (error: AxiosError) => AxiosError | Promise<AxiosError>;

class ApiClient {
  private baseURL: string;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private errorInterceptors: ErrorInterceptor[] = [];

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    
    // Configure axios defaults
    axios.defaults.timeout = 30000;
    axios.defaults.headers.common['Content-Type'] = 'application/json';
  }

  // Interceptor management
  addRequestInterceptor(interceptor: RequestInterceptor) {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: ResponseInterceptor) {
    this.responseInterceptors.push(interceptor);
  }

  addErrorInterceptor(interceptor: ErrorInterceptor) {
    this.errorInterceptors.push(interceptor);
  }

  // Get authentication headers
  private async getAuthHeaders(): Promise<Record<string, string>> {
    // Try to get token from localStorage first
    const storedToken = localStorage.getItem('firebase-token');
    
    if (storedToken) {
      return {
        'Authorization': `Bearer ${storedToken}`,
      };
    }
    
    // Fallback to getting token from Firebase auth
    const auth = getAuth();
    const user = auth.currentUser;
    
    if (!user) {
      throw new AuthError('User not authenticated');
    }
    
    const token = await user.getIdToken();
    
    return {
      'Authorization': `Bearer ${token}`,
    };
  }

  // Retry logic
  private async retryRequest<T>(
    requestFn: () => Promise<T>,
    retries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on auth errors or client errors (4xx)
        if (error instanceof AuthError || 
            (error instanceof ApiError && (error as ApiError).status >= 400 && (error as ApiError).status < 500)) {
          throw error;
        }

        if (attempt === retries) {
          throw error;
        }

        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
      }
    }

    throw lastError!;
  }

  // Main request method
  async request<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      retries = 3,
      retryDelay = 1000,
      timeout = 30000,
      ...requestConfig
    } = config;

    const requestFn = async (): Promise<ApiResponse<T>> => {
      // Apply request interceptors
      let finalConfig = { ...requestConfig };
      for (const interceptor of this.requestInterceptors) {
        finalConfig = await interceptor(finalConfig);
      }

      // Get auth headers
      const authHeaders = await this.getAuthHeaders();
      
      // Prepare request
      const url = `${this.baseURL}${endpoint}`;
      const axiosConfig: AxiosRequestConfig = {
        ...finalConfig,
        url,
        headers: {
          ...authHeaders,
          ...finalConfig.headers,
        },
        timeout,
      };

      try {
        const response: AxiosResponse<T> = await axios.request(axiosConfig);

        // Apply response interceptors
        let finalResponse = response;
        for (const interceptor of this.responseInterceptors) {
          finalResponse = await interceptor(finalResponse);
        }

        return {
          data: finalResponse.data,
          status: finalResponse.status,
          headers: finalResponse.headers as Record<string, string>,
        };
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const axiosError = error as AxiosError;
          let errorMessage = `HTTP ${axiosError.response?.status}: ${axiosError.message}`;
          let errorDetails: unknown = null;

          if (axiosError.response?.data) {
            const errorData = axiosError.response.data as Record<string, unknown>;
            errorMessage = (errorData.detail as string) || (errorData.message as string) || errorMessage;
            errorDetails = errorData;
          }

          const apiError = new ApiError(
            errorMessage,
            axiosError.response?.status || 500,
            (errorDetails as { code?: string })?.code,
            errorDetails
          );

          // Apply error interceptors
          let finalError: AxiosError = axiosError;
          for (const interceptor of this.errorInterceptors) {
            finalError = await interceptor(finalError);
          }

          throw apiError;
        }

        // Handle non-axios errors
        if (error instanceof Error) {
          // Apply error interceptors
          let finalError: Error = error;
          for (const interceptor of this.errorInterceptors) {
            finalError = await interceptor(finalError as AxiosError);
          }

          if (error.name === 'AbortError') {
            throw new NetworkError('Request timeout');
          }

          throw finalError;
        }

        throw new NetworkError('Network error');
      }
    };

    return this.retryRequest(requestFn, retries, retryDelay);
  }

  // Convenience methods
  async get<T>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      data,
    });
  }

  async put<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      data,
    });
  }

  async patch<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PATCH',
      data,
    });
  }

  async delete<T>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }
}

// Create and export the API client instance
export const apiClient = new ApiClient();

// Add default interceptors
apiClient.addRequestInterceptor((config) => {
  // Add request logging in development
  if (process.env.NODE_ENV === 'development') {
    console.log('🔵 Request Interceptor:', {
      method: config.method,
      url: config.url,
      headers: config.headers,
      data: config.data
    });
  }
  return config;
});

apiClient.addResponseInterceptor((response) => {
  // Add response logging in development
  if (process.env.NODE_ENV === 'development') {
    console.log('🟢 Response Interceptor:', {
      status: response.status,
      statusText: response.statusText,
      url: response.config.url,
      data: response.data
    });
  }
  return response;
});

apiClient.addErrorInterceptor((error) => {
  // Log errors
  if (process.env.NODE_ENV === 'development') {
    console.log('Error Interceptor:', {
      message: error.message,
      status: error.response?.status,
      url: error.config?.url,
      data: error.response?.data
    });
  }
  return error;
}); 