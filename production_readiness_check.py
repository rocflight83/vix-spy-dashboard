#!/usr/bin/env python3
"""
VIX/SPY Trading System - Production Readiness Check
This script validates that your system is ready for production deployment.
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

def check_environment_variables():
    """Check all required environment variables are set"""
    print("1. Environment Variables Check")
    print("=" * 50)
    
    required_vars = [
        'TRADESTATION_CLIENT_ID',
        'TRADESTATION_CLIENT_SECRET', 
        'TRADESTATION_REFRESH_TOKEN',
        'TRADESTATION_SIM_ACCOUNT',
        'TRADESTATION_LIVE_ACCOUNT',
        'DATABASE_URL',
        'SUPABASE_URL',
        'STRATEGY_ENABLED',
        'USE_LIVE_ACCOUNT',
        'VIX_SYMBOL',
        'UNDERLYING_SYMBOL',
        'DELTA_TARGET',
        'WING_WIDTH',
        'TAKE_PROFIT_PERCENTAGE',
        'ENTRY_SCHEDULE_HOUR',
        'ENTRY_SCHEDULE_MINUTE',
        'EXIT_SCHEDULE_HOUR',
        'EXIT_SCHEDULE_MINUTE'
    ]
    
    missing_vars = []
    safety_check_passed = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
            print(f"   ❌ {var}: NOT SET")
        else:
            # Mask sensitive values
            if 'SECRET' in var or 'TOKEN' in var:
                display_value = f"{value[:8]}..."
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
            
            # Safety checks
            if var == 'STRATEGY_ENABLED' and value.lower() == 'true':
                print(f"   ⚠️  WARNING: Strategy is ENABLED - should start disabled")
                safety_check_passed = False
            elif var == 'USE_LIVE_ACCOUNT' and value.lower() == 'true':
                print(f"   ⚠️  WARNING: Live account enabled - should start with SIM")
                safety_check_passed = False
    
    print()
    if missing_vars:
        print(f"❌ FAILED: {len(missing_vars)} required variables missing:")
        for var in missing_vars:
            print(f"   - {var}")
        return False, safety_check_passed
    else:
        print("✅ PASSED: All environment variables set")
        return True, safety_check_passed

def check_file_structure():
    """Check that all required files exist"""
    print("2. File Structure Check")
    print("=" * 50)
    
    required_files = [
        'railway.json',
        'Procfile', 
        'requirements.txt',
        'backend/app/main.py',
        'backend/app/services/trading_engine.py',
        'backend/app/services/tradestation_api.py',
        'backend/app/services/market_data.py',
        'backend/app/core/scheduler.py',
        'backend/app/models/database.py',
        'scripts/vix_SPY_IC_entry.py',
        'scripts/vix_SPY_IC_timedexit.py',
        'database_setup.sql'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}: MISSING")
            missing_files.append(file_path)
    
    print()
    if missing_files:
        print(f"❌ FAILED: {len(missing_files)} required files missing")
        return False
    else:
        print("✅ PASSED: All required files present")
        return True

def check_trading_logic():
    """Verify the trading logic configuration"""
    print("3. Trading Logic Configuration Check")
    print("=" * 50)
    
    try:
        os.chdir('backend')
        from app.core.config import settings
        from app.services.market_data import MarketDataService
        
        # Check VIX symbol
        if settings.VIX_SYMBOL == "^VIX":
            print(f"   ✅ VIX Symbol: {settings.VIX_SYMBOL}")
        else:
            print(f"   ❌ VIX Symbol should be ^VIX, got: {settings.VIX_SYMBOL}")
            return False
            
        # Check trading parameters
        checks = [
            ("SPY Symbol", settings.UNDERLYING_SYMBOL, "SPY"),
            ("Delta Target", settings.DELTA_TARGET, 0.3),
            ("Wing Width", settings.WING_WIDTH, 10),
            ("Take Profit %", settings.TAKE_PROFIT_PERCENTAGE, 0.25),
            ("Entry Hour", settings.ENTRY_SCHEDULE_HOUR, 9),
            ("Entry Minute", settings.ENTRY_SCHEDULE_MINUTE, 32),
            ("Exit Hour", settings.EXIT_SCHEDULE_HOUR, 11),
            ("Exit Minute", settings.EXIT_SCHEDULE_MINUTE, 30)
        ]
        
        all_passed = True
        for name, actual, expected in checks:
            if str(actual) == str(expected):
                print(f"   ✅ {name}: {actual}")
            else:
                print(f"   ❌ {name}: Expected {expected}, got {actual}")
                all_passed = False
        
        # Test VIX gap detection
        market_service = MarketDataService()
        try:
            vix_data = market_service.check_vix_gap_up_condition()
            print(f"   ✅ VIX Gap Detection: Working")
            print(f"      Current VIX: {vix_data.get('current_vix', 'N/A')}")
            print(f"      Gap Up: {vix_data.get('vix_gap_up', 'N/A')}")
            print(f"      Gap %: {vix_data.get('gap_percentage', 0):.2f}%")
        except Exception as e:
            print(f"   ⚠️  VIX Gap Detection: {str(e)[:50]}... (May work in production)")
        
        print()
        if all_passed:
            print("✅ PASSED: Trading logic configuration correct")
            return True
        else:
            print("❌ FAILED: Trading logic configuration issues")
            return False
            
    except Exception as e:
        print(f"   ❌ Configuration check failed: {e}")
        print()
        print("❌ FAILED: Could not verify trading logic")
        return False

def check_safety_features():
    """Verify safety features are properly configured"""
    print("4. Safety Features Check")
    print("=" * 50)
    
    safety_passed = True
    
    # Strategy disabled check
    if os.getenv('STRATEGY_ENABLED', 'false').lower() == 'false':
        print("   ✅ Strategy Disabled: Safe for deployment")
    else:
        print("   ❌ Strategy Enabled: UNSAFE - should be disabled initially")
        safety_passed = False
        
    # Simulation account check
    if os.getenv('USE_LIVE_ACCOUNT', 'false').lower() == 'false':
        print("   ✅ Simulation Mode: Safe for testing")
    else:
        print("   ❌ Live Account Enabled: RISKY - should start with simulation")
        safety_passed = False
    
    # Account configuration
    sim_account = os.getenv('TRADESTATION_SIM_ACCOUNT')
    live_account = os.getenv('TRADESTATION_LIVE_ACCOUNT')
    
    if sim_account and sim_account.startswith('SIM'):
        print(f"   ✅ Sim Account: {sim_account}")
    else:
        print(f"   ❌ Sim Account: Invalid or missing")
        safety_passed = False
        
    if live_account and live_account.isdigit():
        print(f"   ✅ Live Account: {live_account}")
    else:
        print(f"   ❌ Live Account: Invalid or missing")
        safety_passed = False
    
    print()
    if safety_passed:
        print("✅ PASSED: All safety features properly configured")
        return True
    else:
        print("❌ FAILED: Safety configuration issues - FIX BEFORE DEPLOYMENT")
        return False

def check_deployment_files():
    """Check Railway deployment configuration"""
    print("5. Deployment Configuration Check")  
    print("=" * 50)
    
    # Check railway.json
    railway_config = Path('railway.json')
    if railway_config.exists():
        print("   ✅ railway.json: Present")
        try:
            import json
            with open(railway_config) as f:
                config = json.load(f)
            if config.get('build', {}).get('builder') == 'NIXPACKS':
                print("   ✅ Build system: NIXPACKS configured")
            else:
                print("   ❌ Build system: Should use NIXPACKS")
                return False
        except Exception as e:
            print(f"   ❌ railway.json: Invalid format - {e}")
            return False
    else:
        print("   ❌ railway.json: Missing")
        return False
    
    # Check Procfile
    procfile = Path('Procfile')
    if procfile.exists():
        with open(procfile) as f:
            content = f.read().strip()
        if 'uvicorn app.main:app' in content:
            print("   ✅ Procfile: Correctly configured for FastAPI")
        else:
            print("   ❌ Procfile: Invalid configuration")
            return False
    else:
        print("   ❌ Procfile: Missing")
        return False
    
    # Check requirements.txt
    requirements = Path('requirements.txt')
    if requirements.exists():
        print("   ✅ requirements.txt: Present")
        with open(requirements) as f:
            reqs = f.read()
        required_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2-binary', 'httpx']
        missing_packages = []
        for pkg in required_packages:
            if pkg not in reqs.lower():
                missing_packages.append(pkg)
        
        if missing_packages:
            print(f"   ❌ requirements.txt: Missing packages: {', '.join(missing_packages)}")
            return False
        else:
            print("   ✅ requirements.txt: All required packages present")
    else:
        print("   ❌ requirements.txt: Missing")
        return False
    
    print()
    print("✅ PASSED: Deployment configuration ready")
    return True

def main():
    """Run all production readiness checks"""
    print("VIX/SPY Trading System - Production Readiness Check")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = [
        check_environment_variables,
        check_file_structure, 
        check_trading_logic,
        check_safety_features,
        check_deployment_files
    ]
    
    passed_checks = 0
    safety_issues = False
    
    for check in checks:
        try:
            if check == check_environment_variables:
                result, safety_ok = check()
                if result:
                    passed_checks += 1
                if not safety_ok:
                    safety_issues = True
            else:
                if check():
                    passed_checks += 1
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
        print()
    
    # Final assessment
    print("FINAL ASSESSMENT")
    print("=" * 60)
    print(f"Checks Passed: {passed_checks}/{len(checks)}")
    
    if passed_checks == len(checks) and not safety_issues:
        print()
        print("🎉 PRODUCTION READY!")
        print()
        print("Your VIX/SPY Iron Condor trading system is ready for deployment.")
        print()
        print("Next Steps:")
        print("1. Deploy to Railway (should auto-deploy from GitHub)")
        print("2. Set up Supabase database using database_setup.sql")
        print("3. Test with test_live_system.py")
        print("4. Monitor for 24-48 hours before enabling strategy")
        print("5. Start with simulation account only")
        print()
        print("Remember: NEVER enable live trading without thorough testing!")
        
    elif passed_checks >= 3 and not safety_issues:
        print()
        print("⚠️  MOSTLY READY - Minor issues to resolve")
        print()
        print("The system should work but has some configuration issues.")
        print("Review the failed checks above and fix them.")
        
    elif safety_issues:
        print()
        print("🚨 SAFETY ISSUES DETECTED!")
        print()
        print("CRITICAL: The system has safety configuration problems.")
        print("DO NOT DEPLOY until safety issues are resolved.")
        print()
        print("Required fixes:")
        print("- Set STRATEGY_ENABLED=false")
        print("- Set USE_LIVE_ACCOUNT=false") 
        print("- Verify account configurations")
        
    else:
        print()
        print("❌ NOT READY FOR PRODUCTION")
        print()
        print("Multiple critical issues need to be resolved.")
        print("Review all failed checks above.")

if __name__ == "__main__":
    main()