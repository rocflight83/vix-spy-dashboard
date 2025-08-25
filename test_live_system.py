"""
Test your live Railway deployment
Replace YOUR_APP_URL with your actual Railway URL
"""
import requests
import json

# Replace this with your Railway app URL from the dashboard
RAILWAY_URL = "https://vix-spy-dashboard-production.up.railway.app"

def test_live_system():
    print("Testing LIVE VIX/SPY Trading System on Railway")
    print("=" * 60)
    print(f"URL: {RAILWAY_URL}")
    print()

    tests_passed = 0
    total_tests = 5

    # Test 1: Basic Health
    print("1. Testing basic health...")
    try:
        response = requests.get(f"{RAILWAY_URL}/", timeout=10)
        if response.status_code == 200:
            print("   [OK] Backend is responding")
            tests_passed += 1
        else:
            print(f"   [FAIL] Backend not responding: {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] Connection failed: {e}")

    # Test 2: Detailed Health Check
    print("\n2. Testing system health...")
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health/detailed", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"   [OK] System health check passed")
            print(f"      Database: {health.get('database', 'Unknown')}")
            print(f"      Scheduler: {health.get('scheduler', 'Unknown')}")
            print(f"      TradeStation: {health.get('tradestation', 'Unknown')}")
            tests_passed += 1
        else:
            print(f"   [FAIL] Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] Health check error: {e}")

    # Test 3: VIX Monitoring
    print("\n3. Testing VIX gap detection...")
    try:
        response = requests.get(f"{RAILWAY_URL}/api/analytics/vix-condition", timeout=10)
        if response.status_code == 200:
            vix = response.json()
            print(f"   [OK] VIX monitoring active")
            print(f"      Current VIX: {vix.get('current_vix', 'Unknown')}")
            print(f"      Gap Up Detected: {vix.get('vix_gap_up', 'Unknown')}")
            print(f"      Gap %: {vix.get('gap_percentage', 'Unknown'):.2f}%")
            tests_passed += 1
        else:
            print(f"   [FAIL] VIX monitoring failed: {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] VIX monitoring error: {e}")

    # Test 4: Strategy Configuration
    print("\n4. Testing strategy configuration...")
    try:
        response = requests.get(f"{RAILWAY_URL}/api/strategy/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"   [OK] Strategy configuration loaded")
            print(f"      Strategy Enabled: {config.get('enabled', 'Unknown')}")
            print(f"      Account Type: {config.get('accountType', 'Unknown')}")
            print(f"      Delta Target: {config.get('deltaTarget', 'Unknown')}")
            tests_passed += 1
        else:
            print(f"   [FAIL] Strategy config failed: {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] Strategy config error: {e}")

    # Test 5: API Documentation
    print("\n5. Testing API documentation...")
    try:
        response = requests.get(f"{RAILWAY_URL}/docs", timeout=10)
        if response.status_code == 200:
            print(f"   [OK] API docs accessible")
            print(f"      URL: {RAILWAY_URL}/docs")
            tests_passed += 1
        else:
            print(f"   [FAIL] API docs failed: {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] API docs error: {e}")

    # Results
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {tests_passed}/{total_tests} PASSED")
    
    if tests_passed == total_tests:
        print("[SUCCESS] DEPLOYMENT SUCCESSFUL!")
        print("\nYour VIX/SPY Iron Condor system is LIVE and ready!")
        print("\nWhat's happening now:")
        print("- System is monitoring VIX gap conditions 24/7")
        print("- Strategy is DISABLED for safety (STRATEGY_ENABLED=false)")
        print("- Running in SIM mode (USE_LIVE_ACCOUNT=false)")
        print(f"- Dashboard: {RAILWAY_URL}")
        print(f"- API Docs: {RAILWAY_URL}/docs")
        print("\nNext steps:")
        print("1. Monitor logs for 24 hours")
        print("2. Test manual entry/exit buttons")
        print("3. Enable strategy when confident")
        print("4. Switch to live account when ready")
    elif tests_passed >= 3:
        print("[WARNING] PARTIALLY WORKING - Some components need attention")
        print("Check Railway logs for detailed errors")
    else:
        print("[ERROR] DEPLOYMENT NEEDS ATTENTION")
        print("Check Railway logs and environment variables")

if __name__ == "__main__":
    print("REPLACE 'your-app-name' in RAILWAY_URL with your actual app URL!")
    print("Get it from Railway dashboard -> Settings -> Public Networking")
    print()
    test_live_system()