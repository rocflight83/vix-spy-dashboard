import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# Add backend to path and change to backend directory to load .env
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))
os.chdir(str(backend_path))

from app.core.config import settings

async def test_database_connection():
    """Test database connection and verify tables"""
    print("Testing Supabase database connection...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(settings.DATABASE_URL)
        print("✓ Database connection successful!")
        
        # Test query
        version = await conn.fetchval("SELECT version()")
        print(f"✓ PostgreSQL version: {version[:50]}...")
        
        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        table_names = [table['table_name'] for table in tables]
        expected_tables = ['trades', 'pdt_tracking', 'strategy_config', 'trade_decisions', 'market_data']
        
        print(f"\n✓ Found {len(table_names)} tables:")
        for table in table_names:
            status = "✓" if table in expected_tables else "?"
            print(f"  {status} {table}")
        
        # Check default config
        config_count = await conn.fetchval("SELECT COUNT(*) FROM strategy_config")
        print(f"\n✓ Strategy config records: {config_count}")
        
        if config_count > 0:
            configs = await conn.fetch("SELECT config_key, config_value FROM strategy_config ORDER BY config_key")
            for config in configs:
                print(f"  - {config['config_key']}: {config['config_value']}")
        
        await conn.close()
        print(f"\n🎉 Database setup is COMPLETE and WORKING!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_database_connection())
    print(f"\nDatabase Status: {'READY' if result else 'NEEDS SETUP'}")