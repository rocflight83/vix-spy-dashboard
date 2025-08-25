# Product Requirements Document (PRD)
# VIX/SPY Iron Condor Automated Trading System

**Version:** 1.0  
**Date:** August 25, 2025  
**Project:** VIX/SPY Iron Condor Trading Dashboard  
**Repository:** https://github.com/rocflight83/vix-spy-dashboard  
**Deployment:** Railway (https://railway.app)

---

## Executive Summary

This document outlines the comprehensive automated trading system for VIX/SPY iron condor strategies. The system monitors VIX gap-up conditions, executes iron condor trades on SPY options, and provides real-time analytics through a web dashboard.

---

## Product Overview

### Core Strategy
- **Entry Condition**: VIX gaps up from previous day's close (`vix_open > vix_previous_close`)
- **Time Execution**: Entry at 9:32 AM ET, forced exit at 11:30 AM ET
- **Options Strategy**: Iron condor on SPY with 0.3 delta targeting and 10-point wings
- **Take Profit**: 25% of maximum profit
- **Account Safety**: PDT compliance for accounts under $25K

### System Architecture
- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: React/Next.js with TypeScript
- **Database**: Supabase PostgreSQL
- **Deployment**: Railway cloud platform
- **Market Data**: Yahoo Finance API
- **Broker Integration**: TradeStation API

---

## Technical Specifications

### Key Components

#### 1. Market Data Service (`backend/app/services/market_data.py`)
```python
# Core VIX gap detection logic
def check_vix_gap_up_condition():
    gap_amount = current_day.open - previous_day.close
    return {'is_gap_up': gap_amount > 0, 'gap_percentage': gap_percentage}
```

#### 2. TradeStation API Integration (`backend/app/services/tradestation_api.py`)
- OAuth refresh token authentication
- Iron condor order construction and placement
- Position management and exit logic
- Real-time account balance and position monitoring

#### 3. Trading Engine (`backend/app/services/trading_engine.py`)
- Main orchestration logic
- Safety checks and PDT compliance
- Trade decision logging
- Error handling and recovery

#### 4. Scheduler (`backend/app/core/scheduler.py`)
- US/Eastern timezone scheduling
- Entry: 9:32 AM ET daily
- Exit: 11:30 AM ET daily
- Market hours validation

#### 5. Dashboard Frontend
- Real-time system monitoring
- Strategy enable/disable controls
- Sim/Live account switching
- Performance analytics and charts
- Trade history and decision logs

---

## Database Schema

### Core Tables

#### trades
```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trade_date DATE NOT NULL,
    entry_time TIMESTAMP WITH TIME ZONE,
    exit_time TIMESTAMP WITH TIME ZONE,
    vix_open DECIMAL(10,4),
    vix_previous_close DECIMAL(10,4),
    gap_percentage DECIMAL(8,4),
    spy_price DECIMAL(10,2),
    put_strike DECIMAL(10,2),
    put_wing_strike DECIMAL(10,2),
    call_strike DECIMAL(10,2),
    call_wing_strike DECIMAL(10,2),
    max_profit DECIMAL(10,4),
    take_profit_target DECIMAL(10,4),
    actual_pnl DECIMAL(10,4),
    status VARCHAR(20),
    account_type VARCHAR(10),
    notes TEXT
);
```

#### system_logs
```sql
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level VARCHAR(20),
    component VARCHAR(50),
    message TEXT,
    trade_id UUID REFERENCES trades(id)
);
```

#### strategy_config
```sql
CREATE TABLE strategy_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    strategy_enabled BOOLEAN DEFAULT false,
    use_live_account BOOLEAN DEFAULT false,
    delta_target DECIMAL(4,2) DEFAULT 0.3,
    wing_width INTEGER DEFAULT 10,
    take_profit_percentage DECIMAL(4,2) DEFAULT 0.25
);
```

---

## Environment Variables

### Production Configuration
```bash
# TradeStation API
TRADESTATION_CLIENT_ID=o4haO6Ax6ZkXwwVJC62bI4rBxfzzgaOM
TRADESTATION_CLIENT_SECRET=it2Rp_nXMkM1bprXqwtbDYJ2awlbzPaX5SsKpq2hrV23agKWdVOSw19kYuJa56ab
TRADESTATION_REFRESH_TOKEN=ffd3jdaM8n_VNrWyWL8qhl2s1lGT12yF-xgdSgCTJRS7n

# Account Configuration
TRADESTATION_SIM_ACCOUNT=SIM2818191M
TRADESTATION_LIVE_ACCOUNT=11804432

# Database
SUPABASE_URL=https://zivoyngpshcudxyjygjp.supabase.co
DATABASE_URL=postgresql://postgres:vixsup%402025@db.zivoyngpshcudxyjygjp.supabase.co:5432/postgres

# Safety Settings (CRITICAL)
STRATEGY_ENABLED=false  # Must be manually enabled
USE_LIVE_ACCOUNT=false  # Start with simulation

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
```

---

## Deployment Guide

### Initial Setup

1. **Railway Configuration**
   ```bash
   # Repository: https://github.com/rocflight83/vix-spy-dashboard
   # Platform: Railway (https://railway.app)
   # Build Command: Automatic
   # Start Command: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

2. **Environment Variables Setup**
   - Copy all variables from `railway_variables.txt`
   - Paste into Railway → Variables tab
   - Ensure `STRATEGY_ENABLED=false` for safety

3. **Database Setup**
   ```sql
   -- Run these SQL commands in Supabase SQL Editor
   -- (See database schema above)
   ```

### Testing Deployment
```python
# Use test_live_system.py to verify deployment
python test_live_system.py
# Update RAILWAY_URL with your actual Railway app URL
```

---

## Operational Procedures

### Daily Operations

#### 1. Pre-Market Checklist (Before 9:30 AM ET)
- [ ] Verify system is online: Check Railway dashboard
- [ ] Confirm database connectivity: Check Supabase logs
- [ ] Validate TradeStation API: Test authentication
- [ ] Review VIX conditions: Check gap detection
- [ ] Confirm account balances: Verify sufficient buying power

#### 2. Market Open Monitoring (9:30-9:35 AM ET)
- [ ] Monitor VIX gap detection logs
- [ ] Watch for entry signal at 9:32 AM ET
- [ ] Verify order placement if conditions met
- [ ] Check option chain data quality
- [ ] Confirm iron condor construction

#### 3. Position Management (9:35 AM - 11:25 AM ET)
- [ ] Monitor take profit conditions
- [ ] Track position Greeks and P&L
- [ ] Watch for early exit opportunities
- [ ] Monitor system health metrics

#### 4. Forced Exit (11:30 AM ET)
- [ ] Confirm exit order execution
- [ ] Verify position closure
- [ ] Record final P&L
- [ ] Log trade summary

#### 5. Post-Market Analysis (After 4:00 PM ET)
- [ ] Review trade performance
- [ ] Analyze decision logs
- [ ] Check system error logs
- [ ] Update strategy notes

### Weekly Maintenance

#### System Health
- [ ] Review Railway deployment logs
- [ ] Check database performance metrics
- [ ] Validate environment variables
- [ ] Test backup and recovery procedures

#### Strategy Analysis
- [ ] Calculate weekly performance metrics
- [ ] Review VIX gap conditions accuracy
- [ ] Analyze entry/exit timing
- [ ] Assess take profit effectiveness

#### API Maintenance
- [ ] Refresh TradeStation tokens if needed
- [ ] Verify option chain data quality
- [ ] Test market data feeds
- [ ] Check for API rate limiting

### Monthly Reviews

#### Performance Assessment
- [ ] Calculate monthly returns
- [ ] Compare against benchmark
- [ ] Analyze drawdowns
- [ ] Review Sharpe ratio

#### Risk Management
- [ ] Validate PDT compliance
- [ ] Review maximum position sizes
- [ ] Assess correlation risks
- [ ] Update risk parameters if needed

#### System Optimization
- [ ] Review error rates
- [ ] Optimize database queries
- [ ] Update dependencies
- [ ] Enhance monitoring alerts

---

## Troubleshooting Guide

### Common Issues

#### 1. VIX Gap Detection Failures
```python
# Check market data service
# Verify Yahoo Finance API connectivity
# Validate VIX symbol configuration
```
**Action Steps:**
- Check `backend/app/services/market_data.py:check_vix_gap_up_condition()`
- Verify `VIX_SYMBOL=^VIX` environment variable
- Test Yahoo Finance API manually

#### 2. TradeStation Authentication Errors
```python
# Token refresh failures
# Invalid client credentials
# Account access issues
```
**Action Steps:**
- Refresh `TRADESTATION_REFRESH_TOKEN`
- Verify client ID/secret are current
- Check account permissions in TradeStation

#### 3. Order Placement Failures
```python
# Insufficient buying power
# Invalid option symbols
# Market closed errors
```
**Action Steps:**
- Check account balance
- Validate option chain data
- Verify market hours

#### 4. Database Connection Issues
```python
# Supabase connectivity problems
# Connection pool exhaustion
# Query timeouts
```
**Action Steps:**
- Check `DATABASE_URL` environment variable
- Verify Supabase service status
- Restart Railway deployment if needed

#### 5. Scheduler Not Firing
```python
# Timezone configuration errors
# Railway deployment sleep mode
# Scheduler service failures
```
**Action Steps:**
- Verify `ENTRY_SCHEDULE_HOUR/MINUTE` settings
- Check Railway usage limits
- Review scheduler logs in `backend/app/core/scheduler.py`

### Emergency Procedures

#### Immediate Trade Exit
```bash
# Manual exit script
python vix_SPY_IC_timedexit.py
```

#### System Shutdown
```bash
# Disable strategy immediately
# Set STRATEGY_ENABLED=false in Railway
# Cancel all pending orders
# Close all positions
```

#### Data Recovery
```sql
-- Backup trade data
SELECT * FROM trades WHERE trade_date >= CURRENT_DATE - INTERVAL '30 days';

-- Backup system logs
SELECT * FROM system_logs WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';
```

---

## Future Enhancements

### Phase 2 Features

#### Advanced Analytics
- [ ] Machine learning VIX prediction models
- [ ] Options Greeks tracking and alerts
- [ ] Risk-adjusted performance metrics
- [ ] Correlation analysis with market indices

#### Enhanced Risk Management
- [ ] Dynamic position sizing based on VIX levels
- [ ] Multi-timeframe exit strategies
- [ ] Volatility-based take profit adjustments
- [ ] Maximum drawdown protection

#### Trading Improvements
- [ ] Multiple expiration strategies
- [ ] Adaptive delta targeting
- [ ] Market regime detection
- [ ] Alternative entry conditions

#### System Enhancements
- [ ] Mobile app interface
- [ ] Real-time push notifications
- [ ] Advanced charting capabilities
- [ ] Automated reporting via email

### Phase 3 Considerations

#### Multi-Strategy Support
- [ ] Iron butterfly variations
- [ ] Credit spread strategies
- [ ] Straddle/strangle implementations
- [ ] Calendar spread strategies

#### Advanced Automation
- [ ] Reinforcement learning optimization
- [ ] Portfolio-level risk management
- [ ] Multi-asset strategy coordination
- [ ] Real-time strategy adaptation

---

## Key Files Reference

### Backend Core Files
- `backend/app/main.py` - FastAPI application entry point
- `backend/app/services/trading_engine.py` - Main trading orchestration
- `backend/app/services/tradestation_api.py` - Broker API integration
- `backend/app/services/market_data.py` - VIX gap detection logic
- `backend/app/core/scheduler.py` - Automated execution timing
- `backend/app/models/database.py` - Database models and schemas

### Frontend Core Files
- `frontend/pages/index.tsx` - Main dashboard page
- `frontend/components/StrategyControls.tsx` - Strategy management UI
- `frontend/components/PerformanceChart.tsx` - Analytics visualization
- `frontend/lib/api.ts` - API client for backend communication
- `frontend/lib/hooks.ts` - React hooks for data management

### Configuration Files
- `railway.json` - Railway deployment configuration
- `Procfile` - Application startup command
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies

### Original Strategy Files
- `vix_SPY_IC_entry.py` - Original entry script logic
- `vix_SPY_IC_timedexit.py` - Original exit script logic

### Testing and Utilities
- `test_live_system.py` - Production deployment testing
- `start_local.py` - Local development server
- `railway_variables.txt` - Environment variables template

---

## Monitoring and Alerts

### Key Metrics to Monitor
1. **System Health**: API response times, error rates, database connectivity
2. **Trading Performance**: Win rate, average P&L, maximum drawdown
3. **Risk Metrics**: Position sizes, account balance, PDT compliance
4. **Operational Metrics**: Order fill rates, execution timing, data quality

### Alert Thresholds
- **Critical**: System down, authentication failures, order rejections
- **Warning**: Slow API responses, unusual VIX conditions, low account balance
- **Info**: Trade executions, daily P&L, system startup/shutdown

---

## Contact and Support

### System Administration
- **Repository**: https://github.com/rocflight83/vix-spy-dashboard
- **Deployment**: Railway dashboard for logs and configuration
- **Database**: Supabase dashboard for data management
- **Broker API**: TradeStation developer portal for API status

### Documentation Updates
This PRD should be updated whenever:
- Strategy parameters are modified
- New features are added
- Deployment procedures change
- Performance benchmarks are adjusted
- Risk management rules are updated

---

**End of Document**

*This PRD serves as the authoritative guide for the VIX/SPY Iron Condor Automated Trading System. All modifications should be documented and version controlled.*