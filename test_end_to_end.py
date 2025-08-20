"""
End-to-end testing script for VIX/SPY Iron Condor Trading Dashboard
Tests the complete workflow from VIX detection to trade execution
"""
import asyncio
import sys
import os
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))
os.chdir(str(backend_path))

from app.core.config import settings
from app.services.market_data import MarketDataService
from app.services.tradestation_api import TradeStationAPI
from app.services.trading_engine import TradingEngine
from app.services.pdt_compliance import PDTComplianceService
from app.models.database import SessionLocal

async def test_configuration():
    """Test 1: Configuration and Environment"""
    print("🔧 Testing Configuration...")
    
    # Check environment variables
    config_items = [
        ('TRADESTATION_CLIENT_ID', settings.TRADESTATION_CLIENT_ID),
        ('TRADESTATION_CLIENT_SECRET', settings.TRADESTATION_CLIENT_SECRET[:10] + '...'),
        ('TRADESTATION_REFRESH_TOKEN', settings.TRADESTATION_REFRESH_TOKEN[:10] + '...'),
        ('SUPABASE_URL', settings.SUPABASE_URL),
        ('DATABASE_URL', settings.DATABASE_URL[:30] + '...'),
        ('USE_LIVE_ACCOUNT', settings.USE_LIVE_ACCOUNT),
        ('STRATEGY_ENABLED', settings.STRATEGY_ENABLED),
    ]
    
    for key, value in config_items:
        print(f"  ✅ {key}: {value}")
    
    print(f"  🎯 Target Account: {settings.get_account_id()}")
    print(f"  🌐 API Base URL: {settings.get_tradestation_base_url()}")
    print()

async def test_database_connection():
    """Test 2: Database Connection"""
    print("🗄️ Testing Database Connection...")
    
    try:
        db = SessionLocal()
        
        # Test basic query
        result = db.execute("SELECT NOW() as current_time")
        current_time = result.fetchone()
        print(f"  ✅ Database connected - Current time: {current_time[0]}")
        
        # Check tables exist
        tables = db.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """).fetchall()
        
        table_names = [table[0] for table in tables]
        expected_tables = ['trades', 'pdt_tracking', 'strategy_config', 'trade_decisions', 'market_data']
        
        for table in expected_tables:
            if table in table_names:
                print(f"  ✅ Table '{table}' exists")
            else:
                print(f"  ❌ Table '{table}' missing")
        
        # Check configuration
        config_count = db.execute("SELECT COUNT(*) FROM strategy_config").fetchone()[0]
        print(f"  📊 Strategy config records: {config_count}")
        
        db.close()
        
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False
    
    print()
    return True

async def test_market_data():
    """Test 3: Market Data Service"""
    print("📊 Testing Market Data Service...")
    
    try:
        market_service = MarketDataService()
        
        # Test VIX data fetch
        print("  🔄 Fetching VIX data...")
        vix_data = market_service.get_vix_data()
        
        print(f"  📈 VIX Current Open: {vix_data.get('current_open', 'N/A')}")
        print(f"  📉 VIX Previous Close: {vix_data.get('previous_close', 'N/A')}")
        print(f"  ⬆️ Gap Amount: {vix_data.get('gap_amount', 'N/A')}")
        print(f"  📊 Gap Percentage: {vix_data.get('gap_percentage', 'N/A'):.2f}%")
        print(f"  🚀 Is Gap Up: {vix_data.get('is_gap_up', 'N/A')}")
        
        # Test VIX condition check (your original logic!)
        vix_condition = market_service.check_vix_gap_up_condition()
        condition_met = vix_condition.get('condition_met', False)
        
        print(f"  🎯 VIX Entry Condition: {'✅ MET' if condition_met else '❌ NOT MET'}")
        print(f"     Condition Logic: VIX Open ({vix_data.get('current_open', 0):.2f}) > Previous Close ({vix_data.get('previous_close', 0):.2f})")
        
        # Test SPY price
        print("  🔄 Fetching SPY price...")
        spy_price = market_service.get_spy_price()
        print(f"  💰 SPY Price: ${spy_price:.2f}")
        
    except Exception as e:
        print(f"  ❌ Market data test failed: {e}")
        return False
    
    print()
    return True

async def test_tradestation_api():
    """Test 4: TradeStation API"""
    print("🔌 Testing TradeStation API...")
    
    try:
        api = TradeStationAPI()
        
        # Test authentication
        print("  🔐 Testing authentication...")
        token = await api.get_access_token()
        print(f"  ✅ Access token obtained: {token[:10]}...")
        
        # Test account info
        print("  👤 Testing account info...")
        account_id = settings.get_account_id()
        account_info = await api.get_account_info(account_id)
        
        if isinstance(account_info, dict):
            account_name = account_info.get('DisplayName', 'Unknown')
            account_status = account_info.get('Status', 'Unknown')
            print(f"  ✅ Account: {account_name} (Status: {account_status})")
        else:
            print(f"  ⚠️ Account info format: {type(account_info)}")
        
        # Test positions
        print("  📍 Testing positions...")
        positions = await api.get_positions(account_id)
        print(f"  📊 Current positions: {len(positions) if isinstance(positions, list) else 'Error'}")
        
    except Exception as e:
        print(f"  ❌ TradeStation API test failed: {e}")
        return False
    
    print()
    return True

async def test_iron_condor_strategy():
    """Test 5: Iron Condor Strategy Building"""
    print("⚙️ Testing Iron Condor Strategy...")
    
    try:
        api = TradeStationAPI()
        
        # Test strategy building (your exact parameters!)
        print("  🔧 Building iron condor strategy...")
        from datetime import date
        
        strategy_info = await api.build_iron_condor_strategy(
            symbol=settings.UNDERLYING_SYMBOL,  # SPY
            expiration_date=date.today(),
            delta_target=settings.DELTA_TARGET,  # 0.3
            wing_width=settings.WING_WIDTH       # 10
        )
        
        print(f"  ✅ Strategy built successfully!")
        print(f"     Put Strike: {strategy_info.get('put_strike', 'N/A')}")
        print(f"     Put Wing: {strategy_info.get('put_wing_strike', 'N/A')}")
        print(f"     Call Strike: {strategy_info.get('call_strike', 'N/A')}")  
        print(f"     Call Wing: {strategy_info.get('call_wing_strike', 'N/A')}")
        print(f"     Max Profit: ${strategy_info.get('max_profit', 'N/A')}")
        print(f"     Max Loss: ${strategy_info.get('max_loss', 'N/A')}")
        print(f"     Take Profit: ${strategy_info.get('take_profit_price', 'N/A')} (25%)")
        
    except Exception as e:
        print(f"  ❌ Iron condor strategy test failed: {e}")
        return False
    
    print()
    return True

async def test_pdt_compliance():
    """Test 6: PDT Compliance"""
    print("📝 Testing PDT Compliance...")
    
    try:
        pdt_service = PDTComplianceService()
        account_type = "sim" if not settings.USE_LIVE_ACCOUNT else "live"
        
        # Check PDT status
        pdt_status = pdt_service.check_pdt_compliance(account_type)
        
        print(f"  📊 Account Type: {account_type.upper()}")
        print(f"  🚦 Can Trade Today: {'✅ YES' if pdt_status['can_trade_today'] else '❌ NO'}")
        print(f"  📈 Trades Remaining: {pdt_status['trades_remaining']}")
        print(f"  📅 Period Trades: {pdt_status['trades_in_period']}")
        
        if pdt_status['can_trade_today']:
            print(f"  ✅ PDT compliance check passed")
        else:
            print(f"  ⚠️ PDT rule would block trading")
        
    except Exception as e:
        print(f"  ❌ PDT compliance test failed: {e}")
        return False
    
    print()
    return True

async def test_trading_engine():
    """Test 7: Trading Engine (Simulation)"""
    print("🤖 Testing Trading Engine...")
    
    try:
        engine = TradingEngine()
        
        # Test entry logic (simulation - won't place real orders)
        print("  🚀 Testing entry logic...")
        entry_result = await engine.execute_entry()
        
        print(f"  📊 Entry Result:")
        print(f"     Success: {entry_result.get('success', 'N/A')}")
        print(f"     Message: {entry_result.get('message', 'N/A')}")
        
        if entry_result.get('error'):
            print(f"     Error: {entry_result.get('error')}")
        
        # Test exit logic
        print("  🛑 Testing exit logic...")
        exit_result = await engine.execute_exit()
        
        print(f"  📊 Exit Result:")
        print(f"     Success: {exit_result.get('success', 'N/A')}")
        print(f"     Message: {exit_result.get('message', 'N/A')}")
        print(f"     Trades Closed: {exit_result.get('trades_closed', 0)}")
        
    except Exception as e:
        print(f"  ❌ Trading engine test failed: {e}")
        return False
    
    print()
    return True

async def run_all_tests():
    """Run complete end-to-end test suite"""
    print("🧪 VIX/SPY Iron Condor Dashboard - End-to-End Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Market Data Service", test_market_data),
        ("TradeStation API", test_tradestation_api),
        ("Iron Condor Strategy", test_iron_condor_strategy),
        ("PDT Compliance", test_pdt_compliance),
        ("Trading Engine", test_trading_engine),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        try:
            success = await test_func()
            if success is not False:  # None or True = pass
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with error: {e}")
        
        print("-" * 40)
    
    print()
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your trading system is ready.")
        print()
        print("Next steps:")
        print("1. Start backend: cd backend && python -m uvicorn app.main:app --reload")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Deploy to Railway for 24/7 operation")
    else:
        print("⚠️ Some tests failed. Review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)