'use client';

import { useVixData, useApiData } from '../lib/hooks';
import { api } from '../lib/api';

export function VixMonitor() {
  const { data: vixData, loading: vixLoading, error: vixError } = useVixData();
  const { data: spyData, loading: spyLoading, error: spyError } = useApiData(
    () => api.getSpyPrice(),
    [],
    true,
    5000
  );

  if (vixLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (vixError) {
    return (
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">VIX Monitor</h3>
        <div className="text-red-600 text-sm">
          Error loading VIX data: {vixError}
        </div>
      </div>
    );
  }

  if (!vixData) {
    return (
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">VIX Monitor</h3>
        <div className="text-gray-500 text-sm">
          No VIX data available
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">VIX Monitor</h3>
        <div className="text-xs text-gray-500">
          Updated: {new Date(vixData.date).toLocaleTimeString()}
        </div>
      </div>

      <div className="space-y-4">
        {/* VIX Current vs Previous */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">VIX Current</p>
            <p className="text-2xl font-bold text-gray-900">
              {vixData.currentOpen.toFixed(2)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Previous Close</p>
            <p className="text-lg font-semibold text-gray-700">
              {vixData.previousClose?.toFixed(2) || 'N/A'}
            </p>
          </div>
        </div>

        {/* Gap Analysis */}
        <div className={`p-3 rounded-lg ${
          vixData.isGapUp ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Gap Analysis</p>
              <p className={`text-xs ${vixData.isGapUp ? 'text-green-700' : 'text-red-700'}`}>
                {vixData.isGapUp ? 'GAP UP DETECTED' : 'NO GAP UP'}
              </p>
            </div>
            <div className="text-right">
              <p className={`text-lg font-bold ${
                vixData.isGapUp ? 'text-green-600' : 'text-red-600'
              }`}>
                {vixData.gapAmount && vixData.gapAmount > 0 ? '+' : ''}{vixData.gapAmount?.toFixed(2) || '0.00'}
              </p>
              <p className={`text-sm ${
                vixData.isGapUp ? 'text-green-600' : 'text-red-600'
              }`}>
                ({vixData.gapPercentage && vixData.gapPercentage > 0 ? '+' : ''}{vixData.gapPercentage?.toFixed(1) || '0.0'}%)
              </p>
            </div>
          </div>
        </div>

        {/* SPY Price */}
        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">SPY Price</p>
            <p className="text-xl font-bold text-blue-600">
              ${spyData?.price?.toFixed(2) || spyLoading ? '...' : 'N/A'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Underlying</p>
            <p className="text-sm text-gray-700">
              {spyError ? 'Error' : 'Real-time'}
            </p>
          </div>
        </div>

        {/* Trading Condition */}
        <div className={`p-3 rounded-lg text-center ${
          vixData.isGapUp && (vixData.gapPercentage || 0) > 5 
            ? 'bg-green-100 border border-green-300' 
            : 'bg-gray-100'
        }`}>
          <p className="text-sm font-medium text-gray-900">Trading Condition</p>
          <p className={`text-lg font-bold ${
            vixData.isGapUp && (vixData.gapPercentage || 0) > 5 
              ? 'text-green-600' 
              : 'text-gray-500'
          }`}>
            {vixData.isGapUp && (vixData.gapPercentage || 0) > 5 
              ? 'ENTRY READY' 
              : 'WAITING'}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            {vixData.isGapUp && (vixData.gapPercentage || 0) > 5 
              ? 'VIX gap > 5% detected' 
              : 'Monitoring for VIX gap up > 5%'}
          </p>
        </div>
      </div>
    </div>
  );
}