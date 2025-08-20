'use client';

interface Trade {
  id: number;
  date: string;
  type: 'Iron Condor';
  status: 'Open' | 'Closed' | 'Expired';
  entryPrice: number;
  exitPrice?: number;
  pnl?: number;
  maxProfit: number;
  maxLoss: number;
  strikes: {
    putSell: number;
    putBuy: number;
    callSell: number;
    callBuy: number;
  };
}

export function TradeHistory() {
  // Mock data - replace with API call
  const trades: Trade[] = [
    {
      id: 1,
      date: '2025-08-19',
      type: 'Iron Condor',
      status: 'Open',
      entryPrice: 2.45,
      maxProfit: 2.45,
      maxLoss: 7.55,
      strikes: {
        putSell: 445,
        putBuy: 435,
        callSell: 465,
        callBuy: 475,
      },
    },
    {
      id: 2,
      date: '2025-08-18',
      type: 'Iron Condor',
      status: 'Closed',
      entryPrice: 2.15,
      exitPrice: 0.65,
      pnl: 1.50,
      maxProfit: 2.15,
      maxLoss: 7.85,
      strikes: {
        putSell: 440,
        putBuy: 430,
        callSell: 460,
        callBuy: 470,
      },
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Open':
        return 'bg-blue-100 text-blue-800';
      case 'Closed':
        return 'bg-green-100 text-green-800';
      case 'Expired':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPnlColor = (pnl?: number) => {
    if (!pnl) return '';
    return pnl > 0 ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Trade History</h3>
        <button className="text-sm text-blue-600 hover:text-blue-700">
          View All
        </button>
      </div>

      <div className="space-y-4">
        {trades.map((trade) => (
          <div key={trade.id} className="border rounded-lg p-4 hover:bg-gray-50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className="font-medium text-gray-900">#{trade.id}</span>
                <span className={`status-indicator ${getStatusColor(trade.status)}`}>
                  {trade.status}
                </span>
              </div>
              <span className="text-sm text-gray-500">{trade.date}</span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm mb-3">
              <div>
                <p className="text-gray-500">Entry Price</p>
                <p className="font-medium">${trade.entryPrice.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-500">
                  {trade.status === 'Open' ? 'Max Profit' : 'P&L'}
                </p>
                <p className={`font-medium ${
                  trade.status === 'Open' 
                    ? 'text-gray-900' 
                    : getPnlColor(trade.pnl)
                }`}>
                  ${trade.status === 'Open' 
                    ? trade.maxProfit.toFixed(2) 
                    : trade.pnl?.toFixed(2) || '0.00'
                  }
                </p>
              </div>
            </div>

            <div className="text-xs text-gray-600">
              <p>
                Put: {trade.strikes.putBuy}/{trade.strikes.putSell} • 
                Call: {trade.strikes.callSell}/{trade.strikes.callBuy}
              </p>
            </div>
          </div>
        ))}

        {trades.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No trades executed yet
          </div>
        )}
      </div>
    </div>
  );
}