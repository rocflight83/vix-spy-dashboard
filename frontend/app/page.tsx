'use client';

import { Toaster } from 'react-hot-toast';
import { TradingStatus } from '../components/TradingStatus';
import { StrategyControls } from '../components/StrategyControls';
import { TradeHistory } from '../components/TradeHistory';
import { VixMonitor } from '../components/VixMonitor';
import { DecisionLog } from '../components/DecisionLog';
import { PerformanceChart } from '../components/PerformanceChart';
import { useStrategy, useSystemHealth, useConnectionStatus } from '../lib/hooks';

export default function Dashboard() {
  const { strategy } = useStrategy();
  const { data: systemHealth } = useSystemHealth();
  const { isConnected, isOnline, apiConnected } = useConnectionStatus();

  return (
    <div className="px-4 py-6 space-y-6">
      <Toaster position="top-right" />
      
      {/* Connection Status Alert */}
      {!isConnected && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-red-400">⚠️</div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Connection Issue
              </h3>
              <p className="text-sm text-red-700 mt-1">
                {!isOnline 
                  ? 'No internet connection detected'
                  : !apiConnected 
                    ? 'Cannot connect to trading server. Check if backend is running.'
                    : 'Connection issues detected'
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                strategy?.enabled ? 'bg-green-100' : 'bg-gray-100'
              }`}>
                <div className={`w-3 h-3 rounded-full ${
                  strategy?.enabled ? 'bg-green-500' : 'bg-gray-400'
                }`} />
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Strategy Status</p>
              <p className={`text-lg font-semibold ${
                strategy?.enabled ? 'text-green-600' : 'text-gray-400'
              }`}>
                {strategy?.enabled ? 'ACTIVE' : 'DISABLED'}
              </p>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full" />
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Account Type</p>
              <p className="text-lg font-semibold text-blue-600">
                {strategy?.accountType?.toUpperCase() || 'LOADING...'}
              </p>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <div className="w-3 h-3 bg-purple-500 rounded-full" />
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Next Entry</p>
              <p className="text-lg font-semibold text-purple-600">
                9:32 AM ET
              </p>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <div className="w-3 h-3 bg-orange-500 rounded-full" />
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Next Exit</p>
              <p className="text-lg font-semibold text-orange-600">
                11:30 AM ET
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <StrategyControls />
        </div>
        <div>
          <TradingStatus status={systemHealth} />
        </div>
      </div>

      {/* VIX Monitor & Current Position */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <VixMonitor />
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Position</h3>
          <div className="text-center py-8 text-gray-500">
            No open positions
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Strategy Performance</h3>
        <PerformanceChart />
      </div>

      {/* Trade History & Decision Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TradeHistory />
        <DecisionLog />
      </div>
    </div>
  );
}