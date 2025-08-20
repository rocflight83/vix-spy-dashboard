/**
 * Custom React hooks for managing API data and state
 */

import { useState, useEffect, useCallback } from 'react';
import { api, ApiResponse, StrategyConfig, Trade, TradeDecision, VixData, SystemHealth, handleApiError } from './api';
import toast from 'react-hot-toast';

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

// Generic hook for API data fetching
export function useApiData<T>(
  fetcher: () => Promise<ApiResponse<T>>,
  dependencies: any[] = [],
  autoRefresh: boolean = false,
  refreshInterval: number = 30000
): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetcher();
      
      if (response.success && response.data) {
        setData(response.data);
      } else {
        const errorMessage = handleApiError(response.error || 'Unknown error');
        setError(errorMessage);
        if (!autoRefresh) { // Don't show toast for background refreshes
          toast.error(errorMessage);
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unexpected error';
      setError(errorMessage);
      if (!autoRefresh) {
        toast.error(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, autoRefresh, refreshInterval]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}

// Strategy configuration hook
export function useStrategy() {
  const { data, loading, error, refetch } = useApiData(
    () => api.getStrategyConfig(),
    [],
    true,
    10000 // Refresh every 10 seconds
  );

  const toggleStrategy = async (enabled: boolean) => {
    const response = await api.toggleStrategy(enabled);
    if (response.success) {
      toast.success(`Strategy ${enabled ? 'enabled' : 'disabled'}`);
      refetch();
    } else {
      toast.error(handleApiError(response.error || 'Failed to toggle strategy'));
    }
    return response;
  };

  const switchAccount = async (accountType: 'sim' | 'live') => {
    const response = await api.switchAccount(accountType);
    if (response.success) {
      toast.success(`Switched to ${accountType.toUpperCase()} account`);
      refetch();
    } else {
      toast.error(handleApiError(response.error || 'Failed to switch account'));
    }
    return response;
  };

  const forceEntryCheck = async () => {
    const response = await api.forceEntryCheck();
    if (response.success) {
      toast.success('Entry check executed');
      refetch();
    } else {
      toast.error(handleApiError(response.error || 'Entry check failed'));
    }
    return response;
  };

  const forceExitCheck = async () => {
    const response = await api.forceExitCheck();
    if (response.success) {
      toast.success('Exit check executed');
      refetch();
    } else {
      toast.error(handleApiError(response.error || 'Exit check failed'));
    }
    return response;
  };

  return {
    strategy: data,
    loading,
    error,
    refetch,
    toggleStrategy,
    switchAccount,
    forceEntryCheck,
    forceExitCheck,
  };
}

// System health hook
export function useSystemHealth() {
  return useApiData(
    () => api.getHealth(),
    [],
    true,
    15000 // Refresh every 15 seconds
  );
}

// VIX data hook
export function useVixData() {
  return useApiData(
    () => api.getVixData(),
    [],
    true,
    5000 // Refresh every 5 seconds during market hours
  );
}

// Trades hook
export function useTrades(limit: number = 50) {
  return useApiData(
    () => api.getTrades(limit),
    [limit],
    true,
    30000 // Refresh every 30 seconds
  );
}

// Open trades hook
export function useOpenTrades() {
  return useApiData(
    () => api.getOpenTrades(),
    [],
    true,
    10000 // Refresh every 10 seconds
  );
}

// Trade decisions hook
export function useTradeDecisions(limit: number = 50) {
  return useApiData(
    () => api.getTradeDecisions(limit),
    [limit],
    true,
    15000 // Refresh every 15 seconds
  );
}

// Performance data hook
export function usePerformance() {
  const stats = useApiData(
    () => api.getPerformanceStats(),
    [],
    true,
    60000 // Refresh every minute
  );

  const history = useApiData(
    () => api.getPerformanceHistory(),
    [],
    true,
    60000 // Refresh every minute
  );

  return {
    stats: stats.data,
    history: history.data,
    loading: stats.loading || history.loading,
    error: stats.error || history.error,
    refetch: () => {
      stats.refetch();
      history.refetch();
    },
  };
}

// PDT status hook
export function usePdtStatus() {
  return useApiData(
    () => api.getPdtStatus(),
    [],
    true,
    30000 // Refresh every 30 seconds
  );
}

// Connection status hook
export function useConnectionStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [apiConnected, setApiConnected] = useState(false);

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

  // Check API connection periodically
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await api.getHealth();
        setApiConnected(response.success);
      } catch {
        setApiConnected(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 10000); // Check every 10 seconds

    return () => clearInterval(interval);
  }, []);

  return {
    isOnline,
    apiConnected,
    isConnected: isOnline && apiConnected,
  };
}