'use client';

import { useState } from 'react';

interface ChartData {
  date: string;
  pnl: number;
  cumulativePnl: number;
  trades: number;
}

export function PerformanceChart() {
  // Mock data - replace with API call using Recharts
  const [data] = useState<ChartData[]>([
    { date: '2025-08-15', pnl: 150, cumulativePnl: 150, trades: 1 },
    { date: '2025-08-16', pnl: -75, cumulativePnl: 75, trades: 1 },
    { date: '2025-08-17', pnl: 200, cumulativePnl: 275, trades: 1 },
    { date: '2025-08-18', pnl: 125, cumulativePnl: 400, trades: 1 },
    { date: '2025-08-19', pnl: -50, cumulativePnl: 350, trades: 1 },
  ]);

  const totalPnL = data[data.length - 1]?.cumulativePnl || 0;
  const totalTrades = data.reduce((sum, day) => sum + day.trades, 0);
  const winRate = data.filter(d => d.pnl > 0).length / data.length * 100;

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">${totalPnL}</p>
          <p className="text-sm text-gray-600">Total P&L</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600">{totalTrades}</p>
          <p className="text-sm text-gray-600">Total Trades</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-purple-600">{winRate.toFixed(0)}%</p>
          <p className="text-sm text-gray-600">Win Rate</p>
        </div>
      </div>

      {/* Simple Chart Placeholder */}
      <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">📈</div>
          <p>Performance Chart</p>
          <p className="text-sm">Cumulative P&L: ${totalPnL}</p>
          <p className="text-xs mt-2">Chart component will be integrated with Recharts</p>
        </div>
      </div>

      {/* Recent Performance Table */}
      <div className="mt-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Recent Performance</h4>
        <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Daily P&L</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cumulative</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Trades</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.slice(-5).map((row, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-3 py-2 text-sm text-gray-900">{row.date}</td>
                  <td className={`px-3 py-2 text-sm font-medium ${
                    row.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ${row.pnl}
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-900">${row.cumulativePnl}</td>
                  <td className="px-3 py-2 text-sm text-gray-900">{row.trades}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}