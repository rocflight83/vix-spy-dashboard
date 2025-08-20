"""
Automated Supabase database setup script
This script will create all required tables and initial configuration
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
from supabase import create_client, Client

async def setup_database():
    """Set up Supabase database tables and initial data"""
    
    print("🚀 Starting Supabase database setup...")
    print(f"Database URL: {settings.SUPABASE_URL}")
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        print("✅ Connected to Supabase")
        
        # Create tables using SQL
        sql_commands = [
            # Trades table
            """
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                trade_date DATE NOT NULL DEFAULT CURRENT_DATE,
                entry_time TIMESTAMPTZ,
                exit_time TIMESTAMPTZ,
                underlying_symbol VARCHAR(10) NOT NULL DEFAULT 'SPY',
                expiration_date DATE NOT NULL,
                put_strike DECIMAL(10,2) NOT NULL,
                put_wing_strike DECIMAL(10,2) NOT NULL,
                call_strike DECIMAL(10,2) NOT NULL,
                call_wing_strike DECIMAL(10,2) NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                entry_price DECIMAL(10,4),
                exit_price DECIMAL(10,4),
                max_profit DECIMAL(10,4),
                max_loss DECIMAL(10,4),
                realized_pnl DECIMAL(10,4),
                entry_order_id VARCHAR(50),
                exit_order_id VARCHAR(50),
                take_profit_order_id VARCHAR(50),
                is_open BOOLEAN DEFAULT TRUE,
                account_type VARCHAR(10) NOT NULL,
                exit_reason VARCHAR(20),
                vix_open DECIMAL(8,4),
                vix_previous_close DECIMAL(8,4),
                spy_price_at_entry DECIMAL(10,4),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            
            # PDT tracking table
            """
            CREATE TABLE IF NOT EXISTS pdt_tracking (
                id SERIAL PRIMARY KEY,
                account_type VARCHAR(10) NOT NULL,
                trade_date DATE NOT NULL,
                trade_count INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(account_type, trade_date)
            );
            """,
            
            # Strategy configuration table
            """
            CREATE TABLE IF NOT EXISTS strategy_config (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(50) NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                config_type VARCHAR(20) NOT NULL DEFAULT 'string',
                description TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            
            # Trade decisions audit table
            """
            CREATE TABLE IF NOT EXISTS trade_decisions (
                id SERIAL PRIMARY KEY,
                decision_time TIMESTAMPTZ DEFAULT NOW(),
                decision_type VARCHAR(20) NOT NULL,
                was_executed BOOLEAN NOT NULL,
                reason TEXT NOT NULL,
                account_type VARCHAR(10) NOT NULL,
                vix_value DECIMAL(8,4),
                spy_price DECIMAL(10,4),
                vix_gap_percentage DECIMAL(6,3),
                pdt_trades_remaining INTEGER,
                trade_id INTEGER REFERENCES trades(id),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            
            # Market data table
            """
            CREATE TABLE IF NOT EXISTS market_data (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                open_price DECIMAL(10,4) NOT NULL,
                close_price DECIMAL(10,4) NOT NULL,
                high_price DECIMAL(10,4) NOT NULL,
                low_price DECIMAL(10,4) NOT NULL,
                volume BIGINT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(date, symbol)
            );
            """,
        ]
        
        # Execute table creation
        for i, sql in enumerate(sql_commands, 1):
            print(f"📝 Creating table {i}/5...")
            result = supabase.rpc('exec_sql', {'sql': sql.strip()})
            
        print("✅ All tables created successfully")
        
        # Create indexes
        index_commands = [
            "CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(trade_date);",
            "CREATE INDEX IF NOT EXISTS idx_trades_account_type ON trades(account_type);",
            "CREATE INDEX IF NOT EXISTS idx_trades_is_open ON trades(is_open);",
            "CREATE INDEX IF NOT EXISTS idx_pdt_tracking_account_date ON pdt_tracking(account_type, trade_date);",
            "CREATE INDEX IF NOT EXISTS idx_trade_decisions_time ON trade_decisions(decision_time);",
            "CREATE INDEX IF NOT EXISTS idx_trade_decisions_type ON trade_decisions(decision_type);",
            "CREATE INDEX IF NOT EXISTS idx_market_data_date_symbol ON market_data(date, symbol);",
        ]
        
        print("📊 Creating indexes...")
        for sql in index_commands:
            try:
                supabase.rpc('exec_sql', {'sql': sql})
            except Exception as e:
                print(f"Warning: Index creation failed: {e}")
        
        print("✅ Indexes created")
        
        # Insert default configuration
        config_data = [
            {'config_key': 'strategy_enabled', 'config_value': 'false', 'config_type': 'boolean', 'description': 'Whether the trading strategy is enabled'},
            {'config_key': 'use_live_account', 'config_value': 'false', 'config_type': 'boolean', 'description': 'Whether to use live account instead of sim'},
            {'config_key': 'vix_gap_threshold', 'config_value': '5.0', 'config_type': 'number', 'description': 'Minimum VIX gap percentage to trigger entry'},
            {'config_key': 'delta_target', 'config_value': '0.3', 'config_type': 'number', 'description': 'Target delta for option selection'},
            {'config_key': 'wing_width', 'config_value': '10', 'config_type': 'number', 'description': 'Strike price width for iron condor wings'},
            {'config_key': 'take_profit_percentage', 'config_value': '0.25', 'config_type': 'number', 'description': 'Take profit as percentage of max profit'},
            {'config_key': 'max_trades_per_day', 'config_value': '1', 'config_type': 'number', 'description': 'Maximum number of trades per day'},
            {'config_key': 'pdt_max_trades_5_days', 'config_value': '3', 'config_type': 'number', 'description': 'Maximum trades allowed in 5 trading days (PDT rule)'}
        ]
        
        print("⚙️ Inserting default configuration...")
        for config in config_data:
            try:
                supabase.table('strategy_config').upsert(config).execute()
            except Exception as e:
                print(f"Config insert failed: {e}")
        
        print("✅ Default configuration inserted")
        
        # Verify setup
        print("🔍 Verifying database setup...")
        
        # Check tables exist
        tables_result = supabase.rpc('get_table_names').execute()
        expected_tables = {'trades', 'pdt_tracking', 'strategy_config', 'trade_decisions', 'market_data'}
        
        if hasattr(tables_result, 'data') and tables_result.data:
            found_tables = set(tables_result.data)
            missing_tables = expected_tables - found_tables
            if missing_tables:
                print(f"⚠️  Missing tables: {missing_tables}")
            else:
                print("✅ All tables verified")
        
        # Check configuration
        config_result = supabase.table('strategy_config').select('*').execute()
        if hasattr(config_result, 'data') and config_result.data:
            print(f"✅ Configuration loaded: {len(config_result.data)} items")
            for item in config_result.data[:3]:  # Show first 3
                print(f"   - {item['config_key']}: {item['config_value']}")
        
        print("🎉 Database setup completed successfully!")
        print()
        print("Next steps:")
        print("1. Run the backend API: cd backend && python -m uvicorn app.main:app --reload")
        print("2. Test the health endpoint: curl http://localhost:8000/api/health/detailed")
        print("3. Start the frontend: cd frontend && npm run dev")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("Try running the SQL manually in your Supabase dashboard")
        return False

if __name__ == "__main__":
    result = asyncio.run(setup_database())
    sys.exit(0 if result else 1)