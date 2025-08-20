'use client';

interface Decision {
  id: number;
  timestamp: string;
  type: 'entry_attempt' | 'exit_attempt';
  executed: boolean;
  reason: string;
  vixGap?: number;
  pdtRemaining?: number;
}

export function DecisionLog() {
  // Mock data - replace with API call
  const decisions: Decision[] = [
    {
      id: 1,
      timestamp: '2025-08-20T09:32:00Z',
      type: 'entry_attempt',
      executed: true,
      reason: 'VIX gap up 7.1% detected - iron condor executed',
      vixGap: 7.1,
      pdtRemaining: 2,
    },
    {
      id: 2,
      timestamp: '2025-08-19T11:30:00Z',
      type: 'exit_attempt',
      executed: true,
      reason: 'Timed exit at 11:30 AM ET',
    },
    {
      id: 3,
      timestamp: '2025-08-19T09:32:00Z',
      type: 'entry_attempt',
      executed: false,
      reason: 'VIX gap up condition not met (gap: 2.3%)',
      vixGap: 2.3,
    },
  ];

  const getDecisionIcon = (type: string, executed: boolean) => {
    if (type === 'entry_attempt') {
      return executed ? '✓ ENTER' : '✗ SKIP';
    } else {
      return executed ? '✓ EXIT' : '✗ HOLD';
    }
  };

  const getDecisionColor = (executed: boolean) => {
    return executed ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Decision Log</h3>
        <button className="text-sm text-blue-600 hover:text-blue-700">
          View All
        </button>
      </div>

      <div className="space-y-3">
        {decisions.map((decision) => (
          <div key={decision.id} className="border-l-4 border-gray-200 pl-4 py-2">
            <div className="flex items-center justify-between mb-1">
              <span className={`text-sm font-medium ${getDecisionColor(decision.executed)}`}>
                {getDecisionIcon(decision.type, decision.executed)}
              </span>
              <span className="text-xs text-gray-500">
                {new Date(decision.timestamp).toLocaleString()}
              </span>
            </div>
            
            <p className="text-sm text-gray-700 mb-1">
              {decision.reason}
            </p>
            
            {(decision.vixGap || decision.pdtRemaining) && (
              <div className="flex space-x-4 text-xs text-gray-600">
                {decision.vixGap && (
                  <span>VIX Gap: {decision.vixGap}%</span>
                )}
                {decision.pdtRemaining && (
                  <span>PDT Remaining: {decision.pdtRemaining}</span>
                )}
              </div>
            )}
          </div>
        ))}

        {decisions.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No decisions logged yet
          </div>
        )}
      </div>
    </div>
  );
}