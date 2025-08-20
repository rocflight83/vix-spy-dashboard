'use client';

import { useStrategy } from '../lib/hooks';
import { useState } from 'react';

export function StrategyControls() {
  const { 
    strategy, 
    loading, 
    error, 
    toggleStrategy, 
    switchAccount, 
    forceEntryCheck, 
    forceExitCheck 
  } = useStrategy();
  
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleToggleStrategy = async () => {
    if (!strategy) return;
    setActionLoading('toggle');
    await toggleStrategy(!strategy.enabled);
    setActionLoading(null);
  };

  const handleAccountToggle = async () => {
    if (!strategy) return;
    setActionLoading('account');
    const newType = strategy.accountType === 'sim' ? 'live' : 'sim';
    await switchAccount(newType);
    setActionLoading(null);
  };

  const handleForceEntry = async () => {
    setActionLoading('entry');
    await forceEntryCheck();
    setActionLoading(null);
  };

  const handleForceExit = async () => {
    setActionLoading('exit');
    await forceExitCheck();
    setActionLoading(null);
  };

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="text-red-600 text-sm">
          Error loading strategy controls: {error}
        </div>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="card">
        <div className="text-gray-500 text-sm">
          No strategy configuration available
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-gray-900">Strategy Controls</h3>
        <div className="text-sm text-gray-500">
          Status: {strategy.enabled ? 'Active' : 'Disabled'}
        </div>
      </div>

      <div className="space-y-6">
        {/* Strategy Enable/Disable */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <h4 className="text-sm font-medium text-gray-900">Strategy Status</h4>
            <p className="text-sm text-gray-600">
              {strategy.enabled ? 'Strategy is actively monitoring VIX conditions' : 'Strategy is disabled'}
            </p>
          </div>
          <button
            onClick={handleToggleStrategy}
            disabled={actionLoading === 'toggle'}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
              strategy.enabled ? 'bg-blue-600' : 'bg-gray-200'
            } ${actionLoading === 'toggle' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                strategy.enabled ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Account Type Toggle */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <h4 className="text-sm font-medium text-gray-900">Account Type</h4>
            <p className="text-sm text-gray-600">
              Currently using {strategy.accountType === 'sim' ? 'simulation' : 'live'} account
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleAccountToggle}
              className={`px-3 py-1 text-xs font-medium rounded-full ${
                strategy.accountType === 'sim'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              SIM
            </button>
            <button
              onClick={handleAccountToggle}
              className={`px-3 py-1 text-xs font-medium rounded-full ${
                strategy.accountType === 'live'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              LIVE
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-4">
          <button 
            onClick={handleForceEntry}
            disabled={actionLoading === 'entry'}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading === 'entry' ? 'Checking...' : 'Force Entry Check'}
          </button>
          <button 
            onClick={handleForceExit}
            disabled={actionLoading === 'exit'}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading === 'exit' ? 'Checking...' : 'Force Exit Check'}
          </button>
        </div>

        {/* Strategy Parameters */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Current Parameters</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Delta Target:</span>
              <span className="ml-2 font-medium">0.3</span>
            </div>
            <div>
              <span className="text-gray-500">Wing Width:</span>
              <span className="ml-2 font-medium">10 pts</span>
            </div>
            <div>
              <span className="text-gray-500">Take Profit:</span>
              <span className="ml-2 font-medium">25%</span>
            </div>
            <div>
              <span className="text-gray-500">Entry Time:</span>
              <span className="ml-2 font-medium">9:32 AM ET</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}