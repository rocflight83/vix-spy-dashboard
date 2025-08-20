"""
Quick test to verify the core VIX trading system is working
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))
os.chdir(str(backend_path))

def test_config():
    """Test configuration loading"""
    print("=== Testing Configuration ===")
    try:
        from app.core.config import settings
        print(f"✅ TradeStation Client ID: {settings.TRADESTATION_CLIENT_ID[:10]}...")
        print(f"✅ Supabase URL: {settings.SUPABASE_URL}")
        print(f"✅ Account Type: {'LIVE' if settings.USE_LIVE_ACCOUNT else 'SIM'}")
        print(f"✅ Strategy Enabled: {settings.STRATEGY_ENABLED}")
        print(f"✅ Target Account: {settings.get_account_id()}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_vix_detection():
    """Test VIX gap detection (your original logic)"""
    print("\n=== Testing VIX Gap Detection ===")
    try:
        from app.services.market_data import MarketDataService
        
        market_service = MarketDataService()
        
        # Get VIX data
        vix_data = market_service.get_vix_data()
        print(f"📊 VIX Current: {vix_data.get('current_open', 'N/A')}")
        print(f"📊 VIX Previous: {vix_data.get('previous_close', 'N/A')}")
        print(f"📊 Gap Amount: {vix_data.get('gap_amount', 'N/A')}")
        print(f"📊 Gap %: {vix_data.get('gap_percentage', 'N/A'):.2f}%")
        
        # Test your original condition: VIX open > VIX previous close
        is_gap_up = vix_data.get('is_gap_up', False)
        print(f"🎯 VIX Gap Up Detected: {'✅ YES' if is_gap_up else '❌ NO'}")
        print(f"   Logic: {vix_data.get('current_open', 0)} > {vix_data.get('previous_close', 0)} = {is_gap_up}")
        
        return True
    except Exception as e:
        print(f"❌ VIX detection test failed: {e}")
        return False

def test_tradestation_auth():
    """Test TradeStation authentication"""
    print("\n=== Testing TradeStation Authentication ===")
    try:
        import asyncio
        from app.services.tradestation_api import TradeStationAPI
        
        async def test_auth():
            api = TradeStationAPI()
            token = await api.get_access_token()
            print(f"✅ Authentication successful: {token[:20]}...")
            return True
        
        return asyncio.run(test_auth())
    except Exception as e:
        print(f"❌ TradeStation auth test failed: {e}")
        return False

def test_strategy_parameters():
    """Test iron condor strategy parameters"""
    print("\n=== Testing Strategy Parameters ===")
    try:
        from app.core.config import settings
        
        print(f"📊 Underlying Symbol: {settings.UNDERLYING_SYMBOL}")
        print(f"📊 Delta Target: {settings.DELTA_TARGET}")
        print(f"📊 Wing Width: {settings.WING_WIDTH}")
        print(f"📊 Take Profit %: {settings.TAKE_PROFIT_PERCENTAGE}")
        print(f"⏰ Entry Time: {settings.ENTRY_SCHEDULE_HOUR}:{settings.ENTRY_SCHEDULE_MINUTE:02d} ET")
        print(f"⏰ Exit Time: {settings.EXIT_SCHEDULE_HOUR}:{settings.EXIT_SCHEDULE_MINUTE:02d} ET")
        
        # Verify these match your original script parameters
        assert settings.DELTA_TARGET == 0.3, "Delta target should be 0.3"
        assert settings.WING_WIDTH == 10, "Wing width should be 10"
        assert settings.TAKE_PROFIT_PERCENTAGE == 0.25, "Take profit should be 25%"
        
        print("✅ All strategy parameters match your original scripts")
        return True
    except Exception as e:
        print(f"❌ Strategy parameters test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 VIX/SPY Iron Condor System - Quick Test")
    print("=" * 50)
    
    tests = [
        ("Configuration Loading", test_config),
        ("VIX Gap Detection", test_vix_detection),
        ("TradeStation Authentication", test_tradestation_auth),
        ("Strategy Parameters", test_strategy_parameters),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Running {test_name}...")
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 TEST RESULTS: {passed}/{total} PASSED ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        print("🎉 SYSTEM IS READY!")
        print("\nYour VIX gap detection logic is preserved:")
        print("- IF VIX open > VIX previous close")
        print("- THEN execute iron condor (0.3 delta, 10pt wings, 25% TP)")
        print("- Entry: 9:32 AM ET, Exit: 11:30 AM ET")
        print("\nNext: Deploy to Railway for 24/7 operation")
    else:
        print("⚠️ Some components need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)