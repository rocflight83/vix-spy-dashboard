'use client';

import { SystemHealth } from '../lib/api';

interface TradingStatusProps {
  status?: SystemHealth | null;
}

export function TradingStatus({ status }: TradingStatusProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'disconnected':
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (!status) {
    return (
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Status</h3>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-lg font-medium text-gray-900 mb-4">System Status</h3>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">FastAPI Backend</span>
          <span className={`status-indicator ${getStatusColor(status.status || 'unknown')}`}>
            {status.status || 'unknown'}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Supabase Database</span>
          <span className={`status-indicator ${getStatusColor(status.database || 'unknown')}`}>
            {status.database || 'unknown'}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Trading Scheduler</span>
          <span className={`status-indicator ${getStatusColor(status.scheduler || 'unknown')}`}>
            {status.scheduler || 'unknown'}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">TradeStation API</span>
          <span className={`status-indicator ${getStatusColor(status.tradestation || 'unknown')}`}>
            {status.tradestation || 'unknown'}
          </span>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Last Health Check</span>
          <span className="text-gray-700">
            {status.timestamp 
              ? new Date(status.timestamp).toLocaleTimeString()
              : 'Never'
            }
          </span>
        </div>
      </div>

      <div className="mt-4">
        <button className="w-full btn-secondary text-sm">
          Refresh Status
        </button>
      </div>
    </div>
  );
}