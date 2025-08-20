from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from app.models.database import get_db, Trade, PDTTracking, MarketData
from app.schemas.analytics_schemas import PerformanceMetrics, ChartData, PDTStatus
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    account_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get comprehensive performance metrics"""
    
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Build query
    query = db.query(Trade).filter(
        Trade.trade_date >= start_date,
        Trade.trade_date <= end_date,
        Trade.is_open == False,  # Only closed trades
        Trade.realized_pnl.isnot(None)
    )
    
    if account_type:
        query = query.filter(Trade.account_type == account_type)
    
    trades = query.all()
    
    if not trades:
        return PerformanceMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            largest_win=0.0,
            largest_loss=0.0,
            max_drawdown=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0,
            period_start=start_date,
            period_end=end_date
        )
    
    # Calculate basic metrics
    total_trades = len(trades)
    pnl_values = [float(trade.realized_pnl) for trade in trades]
    winning_trades = [pnl for pnl in pnl_values if pnl > 0]
    losing_trades = [pnl for pnl in pnl_values if pnl < 0]
    
    total_pnl = sum(pnl_values)
    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
    avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0
    largest_win = max(pnl_values) if pnl_values else 0
    largest_loss = min(pnl_values) if pnl_values else 0
    
    # Calculate max drawdown
    max_drawdown = calculate_max_drawdown(pnl_values)
    
    # Calculate profit factor
    gross_profit = sum(winning_trades) if winning_trades else 0
    gross_loss = abs(sum(losing_trades)) if losing_trades else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Calculate Sharpe ratio (simplified)
    sharpe_ratio = calculate_sharpe_ratio(pnl_values)
    
    return PerformanceMetrics(
        total_trades=total_trades,
        winning_trades=len(winning_trades),
        losing_trades=len(losing_trades),
        win_rate=win_rate,
        total_pnl=total_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        largest_win=largest_win,
        largest_loss=largest_loss,
        max_drawdown=max_drawdown,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe_ratio,
        period_start=start_date,
        period_end=end_date
    )

@router.get("/chart/pnl", response_model=ChartData)
async def get_pnl_chart_data(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    account_type: Optional[str] = Query(None),
    chart_type: str = Query("cumulative"),  # "daily" or "cumulative"
    db: Session = Depends(get_db)
):
    """Get P&L chart data"""
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = db.query(Trade).filter(
        Trade.trade_date >= start_date,
        Trade.trade_date <= end_date,
        Trade.is_open == False,
        Trade.realized_pnl.isnot(None)
    )
    
    if account_type:
        query = query.filter(Trade.account_type == account_type)
    
    trades = query.order_by(Trade.trade_date).all()
    
    # Group by date and calculate P&L
    daily_pnl = {}
    for trade in trades:
        trade_date = trade.trade_date
        if trade_date not in daily_pnl:
            daily_pnl[trade_date] = 0
        daily_pnl[trade_date] += float(trade.realized_pnl)
    
    # Create chart data
    dates = []
    values = []
    cumulative_pnl = 0
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.isoformat())
        
        day_pnl = daily_pnl.get(current_date, 0)
        
        if chart_type == "cumulative":
            cumulative_pnl += day_pnl
            values.append(cumulative_pnl)
        else:  # daily
            values.append(day_pnl)
        
        current_date += timedelta(days=1)
    
    return ChartData(
        labels=dates,
        values=values,
        chart_type=chart_type,
        title=f"{'Cumulative' if chart_type == 'cumulative' else 'Daily'} P&L"
    )

@router.get("/pdt-status", response_model=PDTStatus)
async def get_pdt_status(
    account_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get PDT rule compliance status using PDT service"""
    try:
        from app.services.pdt_compliance import PDTComplianceService
        from app.core.config import settings
        
        # Use current account type if not specified
        if not account_type:
            account_type = "live" if settings.USE_LIVE_ACCOUNT else "sim"
        
        pdt_service = PDTComplianceService()
        pdt_status = pdt_service.check_pdt_compliance(account_type)
        
        return PDTStatus(
            total_day_trades=pdt_status["total_day_trades"],
            max_allowed_trades=pdt_status["max_allowed_trades"],
            trades_remaining=pdt_status["trades_remaining"],
            is_compliant=pdt_status["is_compliant"],
            violation_risk=pdt_status["violation_risk"],
            recent_records=pdt_status["recent_records"]
        )
        
    except Exception as e:
        logger.error(f"Error getting PDT status: {e}")
        # Return safe defaults
        return PDTStatus(
            total_day_trades=0,
            max_allowed_trades=3,
            trades_remaining=3,
            is_compliant=True,
            violation_risk=False,
            recent_records=[]
        )

@router.get("/market-conditions")
async def get_market_conditions(
    days: int = Query(5, le=30),
    db: Session = Depends(get_db)
):
    """Get recent market conditions (VIX data)"""
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    market_data = db.query(MarketData).filter(
        MarketData.data_date >= start_date,
        MarketData.data_date <= end_date,
        MarketData.symbol == "^VIX"
    ).order_by(MarketData.data_date.desc()).all()
    
    return [{
        "date": data.data_date.isoformat(),
        "open": data.open_price,
        "high": data.high_price,
        "low": data.low_price,
        "close": data.close_price,
        "previous_close": data.previous_close,
        "gap_amount": data.gap_amount,
        "gap_percentage": data.gap_percentage
    } for data in market_data]

# Helper functions
def calculate_max_drawdown(pnl_values: List[float]) -> float:
    """Calculate maximum drawdown from P&L series"""
    if not pnl_values:
        return 0.0
    
    cumulative = []
    running_sum = 0
    for pnl in pnl_values:
        running_sum += pnl
        cumulative.append(running_sum)
    
    peak = cumulative[0]
    max_dd = 0.0
    
    for value in cumulative:
        if value > peak:
            peak = value
        
        drawdown = peak - value
        if drawdown > max_dd:
            max_dd = drawdown
    
    return max_dd

def calculate_sharpe_ratio(pnl_values: List[float], risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio (simplified)"""
    if len(pnl_values) < 2:
        return 0.0
    
    import statistics
    
    mean_return = statistics.mean(pnl_values)
    std_return = statistics.stdev(pnl_values)
    
    if std_return == 0:
        return 0.0
    
    # Annualize (assuming daily returns, ~252 trading days)
    annual_mean = mean_return * 252
    annual_std = std_return * (252 ** 0.5)
    
    return (annual_mean - risk_free_rate) / annual_std