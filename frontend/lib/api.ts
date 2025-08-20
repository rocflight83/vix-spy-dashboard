/**
 * API client for VIX/SPY Iron Condor Trading Dashboard
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface StrategyConfig {
  enabled: boolean;
  accountType: 'sim' | 'live';
  vixGapThreshold: number;
  deltaTarget: number;
  wingWidth: number;
  takeProfitPercentage: number;
}

export interface Trade {
  id: number;
  tradeDate: string;
  entryTime?: string;
  exitTime?: string;
  underlyingSymbol: string;
  expirationDate: string;
  putStrike: number;
  putWingStrike: number;
  callStrike: number;
  callWingStrike: number;
  quantity: number;
  entryPrice?: number;
  exitPrice?: number;
  maxProfit?: number;
  maxLoss?: number;
  realizedPnl?: number;
  isOpen: boolean;
  accountType: string;
  exitReason?: string;
  vixOpen?: number;
  vixPreviousClose?: number;
  spyPriceAtEntry?: number;
}

export interface TradeDecision {
  id: number;
  decisionTime: string;
  decisionType: 'entry_attempt' | 'exit_attempt';
  wasExecuted: boolean;
  reason: string;
  accountType: string;
  vixValue?: number;
  spyPrice?: number;
  vixGapPercentage?: number;
  pdtTradesRemaining?: number;
}

export interface VixData {
  currentOpen: number;
  currentHigh: number;
  currentLow: number;
  currentClose: number;
  previousClose?: number;
  gapAmount?: number;
  gapPercentage?: number;
  isGapUp: boolean;
  date: string;
}

export interface SystemHealth {
  status: string;
  database: string;
  scheduler: string;
  tradestation: string;
  timestamp: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // Health and system status
  async getHealth(): Promise<ApiResponse<SystemHealth>> {
    return this.request<SystemHealth>('/api/health/detailed');
  }

  // Strategy configuration
  async getStrategyConfig(): Promise<ApiResponse<StrategyConfig>> {
    return this.request<StrategyConfig>('/api/strategy/config');
  }

  async updateStrategyConfig(config: Partial<StrategyConfig>): Promise<ApiResponse<StrategyConfig>> {
    return this.request<StrategyConfig>('/api/strategy/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async toggleStrategy(enabled: boolean): Promise<ApiResponse<{enabled: boolean}>> {
    return this.request<{enabled: boolean}>('/api/strategy/toggle', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
  }

  async switchAccount(accountType: 'sim' | 'live'): Promise<ApiResponse<{accountType: string}>> {
    return this.request<{accountType: string}>('/api/strategy/account', {
      method: 'POST',
      body: JSON.stringify({ accountType }),
    });
  }

  // Market data
  async getVixData(): Promise<ApiResponse<VixData>> {
    return this.request<VixData>('/api/analytics/vix-condition');
  }

  async getSpyPrice(): Promise<ApiResponse<{price: number}>> {
    return this.request<{price: number}>('/api/analytics/spy-price');
  }

  // Trading
  async forceEntryCheck(): Promise<ApiResponse<{message: string}>> {
    return this.request<{message: string}>('/api/strategy/force-entry', {
      method: 'POST',
    });
  }

  async forceExitCheck(): Promise<ApiResponse<{message: string}>> {
    return this.request<{message: string}>('/api/strategy/force-exit', {
      method: 'POST',
    });
  }

  // Trades
  async getTrades(limit: number = 50): Promise<ApiResponse<Trade[]>> {
    return this.request<Trade[]>(`/api/trades?limit=${limit}`);
  }

  async getOpenTrades(): Promise<ApiResponse<Trade[]>> {
    return this.request<Trade[]>('/api/trades/open');
  }

  async getTrade(id: number): Promise<ApiResponse<Trade>> {
    return this.request<Trade>(`/api/trades/${id}`);
  }

  // Trade decisions
  async getTradeDecisions(limit: number = 50): Promise<ApiResponse<TradeDecision[]>> {
    return this.request<TradeDecision[]>(`/api/trades/decisions?limit=${limit}`);
  }

  // Analytics
  async getPerformanceStats(): Promise<ApiResponse<{
    totalPnl: number;
    totalTrades: number;
    winRate: number;
    averageWin: number;
    averageLoss: number;
    maxDrawdown: number;
  }>> {
    return this.request('/api/analytics/performance');
  }

  async getPerformanceHistory(): Promise<ApiResponse<{
    date: string;
    pnl: number;
    cumulativePnl: number;
    trades: number;
  }[]>> {
    return this.request('/api/analytics/performance-history');
  }

  // PDT compliance
  async getPdtStatus(): Promise<ApiResponse<{
    canTradeToday: boolean;
    tradesRemaining: number;
    tradesInPeriod: number;
    periodStart: string;
  }>> {
    return this.request('/api/analytics/pdt-status');
  }
}

// Export singleton instance
export const api = new ApiClient();

// Custom hooks for React components
export function useApi() {
  return api;
}

// Error handling utilities
export function handleApiError(error: string): string {
  if (error.includes('fetch')) {
    return 'Unable to connect to the trading server. Please check if the backend is running.';
  }
  if (error.includes('401') || error.includes('403')) {
    return 'Authentication failed. Please check your credentials.';
  }
  if (error.includes('500')) {
    return 'Server error. Please try again later or contact support.';
  }
  return error;
}