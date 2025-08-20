from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class TradeResponse(BaseModel):
    id: int
    trade_date: date
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    
    # Position details
    underlying_symbol: str
    expiration_date: date
    
    # Strike prices and quantities
    put_strike: float
    put_wing_strike: float
    call_strike: float
    call_wing_strike: float
    quantity: int
    
    # Trade execution details
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    realized_pnl: Optional[float] = None
    
    # TradeStation order IDs
    entry_order_id: Optional[str] = None
    exit_order_id: Optional[str] = None
    take_profit_order_id: Optional[str] = None
    
    # Trade status and flags
    is_open: bool
    account_type: str
    exit_reason: Optional[str] = None
    
    # Market conditions at entry
    vix_open: Optional[float] = None
    vix_previous_close: Optional[float] = None
    spy_price_at_entry: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TradeDecisionResponse(BaseModel):
    id: int
    decision_date: date
    decision_time: datetime
    decision_type: str
    
    # Decision outcome
    action_taken: bool
    reason: str
    
    # Market conditions at decision time
    vix_value: Optional[float] = None
    vix_gap_up: Optional[bool] = None
    spy_price: Optional[float] = None
    
    # Account and compliance info
    account_type: str
    pdt_trades_remaining: Optional[int] = None
    strategy_enabled: bool
    
    # Additional context
    error_message: Optional[str] = None
    trade_id: Optional[int] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True