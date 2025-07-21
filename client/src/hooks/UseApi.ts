'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient, NetworkError, AuthError } from '@/api/client';
import { UseApiOptions, UseApiReturn } from '@/types/api';

export function useApi<T>(
  apiCall: () => Promise<T>,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const {
    enabled = true,
    refetchOnWindowFocus = false,
    refetchOnReconnect = false,
    retryOnError = true,
    retryCount = 3,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isFetchingRef = useRef(false);
  const retryCountRef = useRef(0);

  const executeApiCall = useCallback(async (): Promise<T> => {
    if (isFetchingRef.current) {
      throw new Error('Request already in progress');
    }

    isFetchingRef.current = true;
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiCall();
      setData(result);
      retryCountRef.current = 0;
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);

      // Don't retry on auth errors or if retry is disabled
      if (err instanceof AuthError || !retryOnError) {
        throw err;
      }

      // Retry logic for network errors
      if (err instanceof NetworkError && retryCountRef.current < retryCount) {
        retryCountRef.current++;
        const delay = Math.pow(2, retryCountRef.current) * 1000; // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        return executeApiCall();
      }

      throw err;
    } finally {
      setIsLoading(false);
      isFetchingRef.current = false;
    }
  }, [apiCall, retryOnError, retryCount]);

  const refetch = useCallback(async () => {
    try {
      await executeApiCall();
    } catch (err) {
      // Error is already set in executeApiCall
      console.error('Refetch failed:', err);
    }
  }, [executeApiCall]);

  const mutate = useCallback((newData: T) => {
    setData(newData);
  }, []);

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      executeApiCall().catch(() => {
        // Error is already handled in executeApiCall
      });
    }
  }, [enabled, executeApiCall]);

  // Refetch on window focus
  useEffect(() => {
    if (!refetchOnWindowFocus) return;

    const handleFocus = () => {
      if (enabled && !isLoading) {
        refetch();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [refetchOnWindowFocus, enabled, isLoading, refetch]);

  // Refetch on reconnect
  useEffect(() => {
    if (!refetchOnReconnect) return;

    const handleOnline = () => {
      if (enabled && !isLoading) {
        refetch();
      }
    };

    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, [refetchOnReconnect, enabled, isLoading, refetch]);

  return {
    data,
    isLoading,
    error,
    refetch,
    mutate,
  };
}

// Specialized hooks for common operations
export function useApiGet<T>(
  endpoint: string,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const apiCall = useCallback(() => apiClient.get<T>(endpoint).then(response => response.data), [endpoint]);
  return useApi(apiCall, options);
}

export function useApiPost<T, D = unknown>(
  endpoint: string,
  data: D,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const apiCall = useCallback(() => apiClient.post<T>(endpoint, data).then(response => response.data), [endpoint, data]);
  return useApi(apiCall, options);
}

export function useApiPut<T, D = unknown>(
  endpoint: string,
  data: D,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const apiCall = useCallback(() => apiClient.put<T>(endpoint, data).then(response => response.data), [endpoint, data]);
  return useApi(apiCall, options);
}

export function useApiDelete<T>(
  endpoint: string,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const apiCall = useCallback(() => apiClient.delete<T>(endpoint).then(response => response.data), [endpoint]);
  return useApi(apiCall, options);
} 