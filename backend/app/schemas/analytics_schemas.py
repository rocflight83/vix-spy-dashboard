from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import date

class PerformanceMetrics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    max_drawdown: float
    profit_factor: float
    sharpe_ratio: float
    period_start: date
    period_end: date

class ChartData(BaseModel):
    labels: List[str]
    values: List[float]
    chart_type: str
    title: str

class PDTStatus(BaseModel):
    total_day_trades: int
    max_allowed_trades: int
    trades_remaining: int
    is_compliant: bool
    violation_risk: bool  # True if close to limit
    recent_records: List[Dict[str, Any]]