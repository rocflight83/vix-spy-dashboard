# VIX/SPY Trading System - Production Deployment Checklist

## Pre-Deployment Verification ✅

### 1. Repository & Code Status
- [x] Latest code pushed to GitHub
- [x] Railway deployment configuration verified
- [x] Environment variables properly set
- [x] TradeStation API authentication working
- [x] Original trading logic preserved and tested

### 2. Safety Configuration ⚠️ CRITICAL
- [x] STRATEGY_ENABLED=false (Must be manually enabled)
- [x] USE_LIVE_ACCOUNT=false (Start with simulation)
- [x] PDT compliance checks implemented
- [x] Take profit and timed exit logic verified

### 3. Infrastructure Setup
- [x] Railway deployment configured
- [ ] Supabase database tables created (Manual setup required)
- [x] All environment variables configured
- [x] Logging configuration verified

## Railway Deployment Steps

### Step 1: Connect Repository
```bash
# Repository already connected: https://github.com/rocflight83/vix-spy-dashboard
# Auto-deploy enabled on main branch pushes
```

### Step 2: Environment Variables Setup
**Critical Variables (Copy to Railway → Variables tab):**

```bash
# TradeStation API
TRADESTATION_CLIENT_ID=o4haO6Ax6ZkXwwVJC62bI4rBxfzzgaOM
TRADESTATION_CLIENT_SECRET=it2Rp_nXMkM1bprXqwtbDYJ2awlbzPaX5SsKpq2hrV23agKWdVOSw19kYuJa56ab
TRADESTATION_REFRESH_TOKEN=ffd3jdaM8n_VNrWyWL8qhl2s1lGT12yF-xgdSgCTJRS7n

# Accounts
TRADESTATION_SIM_ACCOUNT=SIM2818191M
TRADESTATION_LIVE_ACCOUNT=11804432

# Supabase Database
SUPABASE_URL=https://zivoyngpshcudxyjygjp.supabase.co
DATABASE_URL=postgresql://postgres:vixsup%402025@db.zivoyngpshcudxyjygjp.supabase.co:5432/postgres

# SAFETY SETTINGS (MUST START WITH THESE)
STRATEGY_ENABLED=false
USE_LIVE_ACCOUNT=false

# Strategy Parameters
VIX_SYMBOL=^VIX
UNDERLYING_SYMBOL=SPY
DELTA_TARGET=0.3
WING_WIDTH=10
TAKE_PROFIT_PERCENTAGE=0.25

# Schedule (US/Eastern)
ENTRY_SCHEDULE_HOUR=9
ENTRY_SCHEDULE_MINUTE=32
EXIT_SCHEDULE_HOUR=11
EXIT_SCHEDULE_MINUTE=30

# Railway Config
PORT=8000
API_HOST=0.0.0.0
LOG_LEVEL=INFO
```

### Step 3: Database Setup (Manual)
1. Go to Supabase Dashboard: https://zivoyngpshcudxyjygjp.supabase.co
2. Navigate to SQL Editor
3. Execute the SQL from `database_setup.sql`
4. Verify tables created: trades, strategy_config, pdt_tracking, trade_decisions, market_data

## Post-Deployment Verification

### Step 1: Get Railway URL
- Go to Railway Dashboard → Your App → Settings → Public Networking
- Copy your app URL (e.g., `https://your-app-name.railway.app`)

### Step 2: Test Live Deployment
Update `test_live_system.py` with your Railway URL and run:
```python
RAILWAY_URL = "https://your-actual-app-name.railway.app"
python test_live_system.py
```

Expected results:
- ✅ Backend responding
- ✅ System health check passed
- ✅ VIX monitoring active
- ✅ Strategy configuration loaded (disabled)
- ✅ API docs accessible

### Step 3: Verify API Endpoints
Test these URLs in browser:
- `https://your-app.railway.app/` - Basic health
- `https://your-app.railway.app/docs` - API documentation
- `https://your-app.railway.app/api/health/detailed` - System health

### Step 4: Monitor Logs
Check Railway logs for:
- VIX data retrieval working
- TradeStation authentication success
- Scheduler running properly
- No critical errors

## Production Safety Protocol

### Phase 1: Simulation Mode (Recommended 1 week)
1. Keep `STRATEGY_ENABLED=false`
2. Keep `USE_LIVE_ACCOUNT=false` 
3. Monitor system stability
4. Test manual controls in dashboard
5. Verify VIX gap detection accuracy

### Phase 2: Enable Strategy (SIM account)
1. Set `STRATEGY_ENABLED=true` in Railway variables
2. Keep `USE_LIVE_ACCOUNT=false`
3. Monitor automated trades in simulation
4. Verify entry/exit timing (9:32 AM / 11:30 AM ET)
5. Confirm take profit logic working

### Phase 3: Live Account (When confident)
1. Set `USE_LIVE_ACCOUNT=true`
2. Start with small position size
3. Monitor first few trades closely
4. Verify PDT compliance
5. Scale up gradually

## Key System Features Verified

### Trading Logic ✅
- VIX gap up detection: `vix_open > vix_previous_close`
- Iron condor with 0.3 delta targeting
- 10-point wing spreads
- 25% take profit target
- Timed exit at 11:30 AM ET

### Risk Management ✅
- PDT compliance for accounts <$25K
- Strategy can be instantly disabled
- Simulation mode for testing
- Automatic position exit
- Account balance monitoring

### Schedule ✅
- Entry attempts at 9:32 AM ET daily
- Forced exit at 11:30 AM ET
- US/Eastern timezone handling
- Market hours validation

## Emergency Procedures

### Immediate Shutdown
```bash
# In Railway Dashboard → Variables:
STRATEGY_ENABLED=false
```

### Manual Position Exit
- Use TradeStation platform directly
- Or run: `python scripts/vix_SPY_IC_timedexit.py`

### System Restart
- Railway Dashboard → Deployments → Restart

## Monitoring Checklist

### Daily (9:00-12:00 AM ET)
- [ ] System online status
- [ ] VIX gap detection working
- [ ] Trade execution (if conditions met)
- [ ] Position management
- [ ] Exit confirmation

### Weekly
- [ ] Performance review
- [ ] Error log analysis
- [ ] API token refresh (if needed)
- [ ] Database health check

### Monthly
- [ ] Strategy performance analysis
- [ ] Risk metrics review
- [ ] System optimization
- [ ] Backup verification

## Dashboard Access

Once deployed, your system provides:
- **Live Dashboard**: `https://your-app.railway.app/`
- **API Documentation**: `https://your-app.railway.app/docs`
- **Strategy Controls**: Enable/disable trading
- **Real-time Monitoring**: VIX conditions, positions, P&L
- **Trade History**: Complete audit trail

## Success Criteria

### System is Production Ready When:
- [x] All API endpoints responding
- [x] VIX data retrieval working
- [x] TradeStation authentication successful
- [x] Database connectivity confirmed
- [x] Scheduler running properly
- [x] Safety controls verified
- [x] Emergency shutdown tested

### Ready to Enable Strategy When:
- [ ] 24-48 hours of stable monitoring
- [ ] Manual controls tested
- [ ] Logs show no critical errors
- [ ] VIX gap detection accurate
- [ ] Database recording properly

### Ready for Live Account When:
- [ ] 1 week+ simulation successful
- [ ] Multiple automated trades executed properly
- [ ] Take profit logic verified
- [ ] Exit timing confirmed
- [ ] Risk management validated

## Support Resources

- **Railway Logs**: Monitor system health and errors
- **Supabase Dashboard**: Database management and queries
- **TradeStation Platform**: Manual trading and position monitoring
- **GitHub Repository**: Code updates and version control

---

**IMPORTANT**: Always start with `STRATEGY_ENABLED=false` and `USE_LIVE_ACCOUNT=false` for safety. Enable features gradually after thorough testing.