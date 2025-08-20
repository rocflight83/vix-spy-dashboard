# VIX/SPY Iron Condor Trading Dashboard

Automated trading system for VIX gap up iron condor strategy on TradeStation.

## Features

- **VIX Gap Detection**: Monitors VIX open > previous close condition
- **Iron Condor Execution**: 0.3 delta targeting, 10-point wings, 25% take profit
- **Automated Scheduling**: 9:32 AM ET entry, 11:30 AM ET exit
- **PDT Compliance**: Respects pattern day trading rules
- **Real-time Dashboard**: Strategy monitoring and controls
- **Cloud Deployment**: 24/7 operation on Railway

## Quick Deploy to Railway

1. Fork this repository to your GitHub
2. Connect to Railway at [railway.app](https://railway.app)
3. Deploy from GitHub repo
4. Set environment variables (see `.env.example`)
5. Enable strategy when ready

## Environment Variables

See `deploy_to_railway.md` for complete setup guide.

## Local Development

```bash
python simple_test.py  # Test system
python start_local.py  # Run locally
```

## Architecture

- **Backend**: FastAPI with SQLAlchemy, APScheduler
- **Database**: Supabase (PostgreSQL)
- **Frontend**: Next.js with TypeScript
- **Trading**: TradeStation API integration
- **Deployment**: Railway platform

## Safety Features

- Environment-based configuration
- PDT rule compliance
- Trade decision audit logging
- Strategy enable/disable controls
- Simulation mode testing