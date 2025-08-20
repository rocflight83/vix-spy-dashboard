from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime, date
from app.core.config import settings

Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_date = Column(Date, nullable=False, default=date.today)
    entry_time = Column(DateTime, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    
    # Position details
    underlying_symbol = Column(String, nullable=False, default="SPY")
    expiration_date = Column(Date, nullable=False)
    
    # Strike prices and quantities
    put_strike = Column(Float, nullable=False)
    put_wing_strike = Column(Float, nullable=False)
    call_strike = Column(Float, nullable=False)
    call_wing_strike = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    
    # Trade execution details
    entry_price = Column(Float, nullable=True)  # Credit received
    exit_price = Column(Float, nullable=True)   # Debit paid
    max_profit = Column(Float, nullable=True)
    max_loss = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    
    # TradeStation order IDs
    entry_order_id = Column(String, nullable=True)
    exit_order_id = Column(String, nullable=True)
    take_profit_order_id = Column(String, nullable=True)
    
    # Trade status and flags
    is_open = Column(Boolean, default=True)
    account_type = Column(String, nullable=False)  # "sim" or "live"
    exit_reason = Column(String, nullable=True)  # "take_profit", "timed_exit", "manual"
    
    # Market conditions at entry
    vix_open = Column(Float, nullable=True)
    vix_previous_close = Column(Float, nullable=True)
    spy_price_at_entry = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PDTTracking(Base):
    __tablename__ = "pdt_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_date = Column(Date, nullable=False, default=date.today)
    account_type = Column(String, nullable=False)  # "sim" or "live"
    trade_count = Column(Integer, default=0)  # Number of day trades on this date
    is_pdt_violation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class StrategyConfig(Base):
    __tablename__ = "strategy_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, unique=True, nullable=False)
    config_value = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TradeDecision(Base):
    __tablename__ = "trade_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    decision_date = Column(Date, nullable=False, default=date.today)
    decision_time = Column(DateTime, nullable=False, default=func.now())
    decision_type = Column(String, nullable=False)  # "entry_attempt", "exit_attempt"
    
    # Decision outcome
    action_taken = Column(Boolean, nullable=False)  # True if trade executed, False if skipped
    reason = Column(String, nullable=False)  # Reason for action or skip
    
    # Market conditions at decision time
    vix_value = Column(Float, nullable=True)
    vix_gap_up = Column(Boolean, nullable=True)
    spy_price = Column(Float, nullable=True)
    
    # Account and compliance info
    account_type = Column(String, nullable=False)
    pdt_trades_remaining = Column(Integer, nullable=True)
    strategy_enabled = Column(Boolean, nullable=False)
    
    # Additional context
    error_message = Column(Text, nullable=True)
    trade_id = Column(Integer, nullable=True)  # Links to Trade if executed
    
    created_at = Column(DateTime, default=func.now())

class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_date = Column(Date, nullable=False, default=date.today)
    symbol = Column(String, nullable=False)
    
    # OHLC data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=True)
    
    # Derived fields
    previous_close = Column(Float, nullable=True)
    gap_amount = Column(Float, nullable=True)  # open - previous_close
    gap_percentage = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=func.now())

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)