@echo off
echo Adding remaining Railway environment variables...

REM Remaining variables after STRATEGY_ENABLED
railway variables set USE_LIVE_ACCOUNT=false
railway variables set VIX_SYMBOL=^VIX
railway variables set UNDERLYING_SYMBOL=SPY
railway variables set DELTA_TARGET=0.3
railway variables set WING_WIDTH=10
railway variables set TAKE_PROFIT_PERCENTAGE=0.25
railway variables set ENTRY_SCHEDULE_HOUR=9
railway variables set ENTRY_SCHEDULE_MINUTE=32
railway variables set EXIT_SCHEDULE_HOUR=11
railway variables set EXIT_SCHEDULE_MINUTE=30
railway variables set PORT=8000
railway variables set API_HOST=0.0.0.0
railway variables set LOG_LEVEL=INFO

echo.
echo All remaining variables added successfully!
echo.
echo You can verify with: railway variables
pause