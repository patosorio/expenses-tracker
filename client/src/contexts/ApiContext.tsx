'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiClient, ApiError, NetworkError, AuthError } from '@/api/client';
import { useAuth } from './AuthContext';
import { AxiosError } from 'axios';

interface ApiContextType {
  isOnline: boolean;
  isAuthenticated: boolean;
  globalError: string | null;
  clearGlobalError: () => void;
  addRequestInterceptor: (interceptor: unknown) => void;
  addResponseInterceptor: (interceptor: unknown) => void;
  addErrorInterceptor: (interceptor: unknown) => void;
}

const ApiContext = createContext<ApiContextType>({
  isOnline: true,
  isAuthenticated: false,
  globalError: null,
  clearGlobalError: () => {},
  addRequestInterceptor: () => {},
  addResponseInterceptor: () => {},
  addErrorInterceptor: () => {},
});

export const useApi = () => useContext(ApiContext);

interface ApiProviderProps {
  children: ReactNode;
}

export const ApiProvider = ({ children }: ApiProviderProps) => {
  const [isOnline, setIsOnline] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const { user } = useAuth();

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Add global error interceptor
  useEffect(() => {
    const errorInterceptor = (error: AxiosError) => {
      if (error instanceof AuthError) {
        // Handle auth errors globally
        console.error('Auth error:', error.message);
        // You might want to redirect to login or refresh token
      } else if (error instanceof NetworkError) {
        // Handle network errors globally
        console.error('Network error:', error.message);
        setGlobalError('Network connection error. Please check your internet connection.');
      } else if (error instanceof ApiError) {
        // Handle API errors globally
        console.error('API error:', error.message);
        setGlobalError(error.message);
      }
      return error;
    };

    apiClient.addErrorInterceptor(errorInterceptor);

    return () => {
      // Note: In a real implementation, you'd want to remove the interceptor
      // but our current implementation doesn't support removal
    };
  }, []);

  // Add request interceptor for authentication
  useEffect(() => {
    const requestInterceptor = (config: any) => {
      // Add any global request headers or modifications here
      if (process.env.NODE_ENV === 'development') {
        console.log('ApiContext Request Interceptor:', {
          url: config.url,
          method: config.method,
          hasAuth: !!config.headers?.Authorization
        });
      }
      return config;
    };

    apiClient.addRequestInterceptor(requestInterceptor);
  }, []);

  // Add response interceptor for common handling
  useEffect(() => {
    const responseInterceptor = (response: any) => {
      // Handle common response patterns here
      if (process.env.NODE_ENV === 'development') {
        console.log('🟢 ApiContext Response Interceptor:', {
          status: response.status,
          url: response.config.url,
          dataType: typeof response.data
        });
      }
      return response;
    };

    apiClient.addResponseInterceptor(responseInterceptor);
  }, []);

  const clearGlobalError = () => {
    setGlobalError(null);
  };

  const addRequestInterceptor = (interceptor: unknown) => {
    apiClient.addRequestInterceptor(interceptor as any);
  };

  const addResponseInterceptor = (interceptor: unknown) => {
    apiClient.addResponseInterceptor(interceptor as any);
  };

  const addErrorInterceptor = (interceptor: unknown) => {
    apiClient.addErrorInterceptor(interceptor as any);
  };

  return (
    <ApiContext.Provider
      value={{
        isOnline,
        isAuthenticated: !!user,
        globalError,
        clearGlobalError,
        addRequestInterceptor,
        addResponseInterceptor,
        addErrorInterceptor,
      }}
    >
      {children}
    </ApiContext.Provider>
  );
}; 