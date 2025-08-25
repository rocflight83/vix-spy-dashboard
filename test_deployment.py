"""
Test your Railway deployment
Replace YOUR_APP_URL with your actual Railway URL
"""
import requests
import json

# Replace with your Railway URL
RAILWAY_URL = "https://your-app.railway.app"

def test_deployment():
    """Test key endpoints"""
    print("Testing Railway deployment...")
    print(f"Base URL: {RAILWAY_URL}")
    print("-" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health/detailed", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Health check passed")
            print(f"   Database: {health.get('database', 'Unknown')}")
            print(f"   Scheduler: {health.get('scheduler', 'Unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: API docs
    print("\n2. Testing API documentation...")
    try:
        response = requests.get(f"{RAILWAY_URL}/docs", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ API docs accessible at {RAILWAY_URL}/docs")
        else:
            print(f"   ❌ API docs failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API docs error: {e}")
    
    # Test 3: VIX data
    print("\n3. Testing VIX monitoring...")
    try:
        response = requests.get(f"{RAILWAY_URL}/api/analytics/vix-condition", timeout=10)
        if response.status_code == 200:
            vix_data = response.json()
            print(f"   ✅ VIX monitoring active")
            print(f"   VIX Gap Up: {vix_data.get('vix_gap_up', 'Unknown')}")
            print(f"   Current VIX: {vix_data.get('current_vix', 'Unknown')}")
        else:
            print(f"   ❌ VIX monitoring failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ VIX monitoring error: {e}")
    
    print("\n" + "=" * 50)
    print("If all tests pass, your system is live!")
    print("Next steps:")
    print("1. Monitor for 24-48 hours in disabled mode")
    print("2. Enable strategy when confident")
    print("3. Switch to live account when ready")

if __name__ == "__main__":
    test_deployment()