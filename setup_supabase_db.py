"""
Script to set up Supabase database tables using SQL execution
Run this once to initialize your database schema
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path and change to backend directory to load .env
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))
os.chdir(str(backend_path))

from app.core.config import settings

def get_database_schema():
    """Return the complete database schema SQL"""
    return """
-- VIX/SPY Iron Condor Trading Dashboard Database Schema
-- Enable Row Level Security
ALTER DATABASE postgres SET timezone = 'UTC';

-- Trades table - stores all trade execution records
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL DEFAULT CURRENT_DATE,
    entry_time TIMESTAMP WITH TIME ZONE,
    exit_time TIMESTAMP WITH TIME ZONE,
    
    -- Position details
    underlying_symbol VARCHAR(10) NOT NULL DEFAULT 'SPY',
    expiration_date DATE NOT NULL,
    
    -- Strike prices and quantities
    put_strike DECIMAL(10,2) NOT NULL,
    put_wing_strike DECIMAL(10,2) NOT NULL,
    call_strike DECIMAL(10,2) NOT NULL,
    call_wing_strike DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    
    -- Trade execution details
    entry_price DECIMAL(10,4), -- Credit received
    exit_price DECIMAL(10,4),  -- Debit paid
    max_profit DECIMAL(10,4),
    max_loss DECIMAL(10,4),
    realized_pnl DECIMAL(10,4),
    
    -- TradeStation order IDs
    entry_order_id VARCHAR(50),
    exit_order_id VARCHAR(50),
    take_profit_order_id VARCHAR(50),
    
    -- Trade status and flags
    is_open BOOLEAN DEFAULT TRUE,
    account_type VARCHAR(10) NOT NULL, -- 'sim' or 'live'
    exit_reason VARCHAR(20), -- 'take_profit', 'timed_exit', 'manual'
    
    -- Market conditions at entry
    vix_open DECIMAL(8,4),
    vix_previous_close DECIMAL(8,4),
    spy_price_at_entry DECIMAL(10,4),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PDT tracking table - Pattern Day Trading compliance
CREATE TABLE IF NOT EXISTS pdt_tracking (
    id SERIAL PRIMARY KEY,
    account_type VARCHAR(10) NOT NULL, -- 'sim' or 'live'
    trade_date DATE NOT NULL,
    trade_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(account_type, trade_date)
);

-- Strategy configuration table
CREATE TABLE IF NOT EXISTS strategy_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL DEFAULT 'string', -- 'string', 'boolean', 'number'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trade decisions audit table - tracks all trading decisions
CREATE TABLE IF NOT EXISTS trade_decisions (
    id SERIAL PRIMARY KEY,
    decision_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decision_type VARCHAR(20) NOT NULL, -- 'entry_attempt', 'exit_attempt'
    was_executed BOOLEAN NOT NULL,
    reason TEXT NOT NULL,
    account_type VARCHAR(10) NOT NULL,
    
    -- Market context
    vix_value DECIMAL(8,4),
    spy_price DECIMAL(10,4),
    vix_gap_percentage DECIMAL(6,3),
    
    -- PDT context
    pdt_trades_remaining INTEGER,
    
    -- Trade context (if executed)
    trade_id INTEGER REFERENCES trades(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market data table - stores VIX and SPY data for analysis
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    open_price DECIMAL(10,4) NOT NULL,
    close_price DECIMAL(10,4) NOT NULL,
    high_price DECIMAL(10,4) NOT NULL,
    low_price DECIMAL(10,4) NOT NULL,
    volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(date, symbol)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(trade_date);
CREATE INDEX IF NOT EXISTS idx_trades_account_type ON trades(account_type);
CREATE INDEX IF NOT EXISTS idx_trades_is_open ON trades(is_open);
CREATE INDEX IF NOT EXISTS idx_pdt_tracking_account_date ON pdt_tracking(account_type, trade_date);
CREATE INDEX IF NOT EXISTS idx_trade_decisions_time ON trade_decisions(decision_time);
CREATE INDEX IF NOT EXISTS idx_trade_decisions_type ON trade_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_market_data_date_symbol ON market_data(date, symbol);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategy_config_updated_at BEFORE UPDATE ON strategy_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default configuration values
INSERT INTO strategy_config (config_key, config_value, config_type, description) VALUES
    ('strategy_enabled', 'false', 'boolean', 'Whether the trading strategy is enabled'),
    ('use_live_account', 'false', 'boolean', 'Whether to use live account instead of sim'),
    ('vix_gap_threshold', '5.0', 'number', 'Minimum VIX gap percentage to trigger entry'),
    ('delta_target', '0.3', 'number', 'Target delta for option selection'),
    ('wing_width', '10', 'number', 'Strike price width for iron condor wings'),
    ('take_profit_percentage', '0.25', 'number', 'Take profit as percentage of max profit'),
    ('max_trades_per_day', '1', 'number', 'Maximum number of trades per day'),
    ('pdt_max_trades_5_days', '3', 'number', 'Maximum trades allowed in 5 trading days (PDT rule)')
ON CONFLICT (config_key) DO NOTHING;

COMMIT;
"""

def print_setup_instructions():
    """Print manual setup instructions"""
    print("=" * 60)
    print("SUPABASE DATABASE SETUP INSTRUCTIONS")
    print("=" * 60)
    print()
    print("Since direct connection failed, please set up manually:")
    print()
    print("1. Go to your Supabase dashboard:")
    print(f"   {settings.SUPABASE_URL}")
    print()
    print("2. Navigate to SQL Editor")
    print()
    print("3. Create a new query and paste the SQL schema")
    print("   (The schema will be copied to database_setup.sql)")
    print()
    print("4. Click 'Run' to execute the schema")
    print()
    print("5. Go to 'Table Editor' to verify tables were created:")
    print("   - trades")
    print("   - pdt_tracking") 
    print("   - strategy_config")
    print("   - trade_decisions")
    print("   - market_data")
    print()
    print("6. Check strategy_config table has default values")
    print()
    print("Once complete, run the backend API to test connectivity.")
    print("=" * 60)

def create_setup_file():
    """Create SQL file for manual setup"""
    sql_content = get_database_schema()
    
    # Write to database_setup.sql
    setup_file = Path(__file__).parent / "database_setup.sql"
    with open(setup_file, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print(f"✓ Database schema saved to: {setup_file}")
    return setup_file

if __name__ == "__main__":
    print("Setting up Supabase database schema...")
    print(f"Database URL: {settings.DATABASE_URL[:50]}...")
    
    # Create setup file
    setup_file = create_setup_file()
    
    # Print instructions
    print_setup_instructions()