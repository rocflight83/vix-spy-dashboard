# Railway Deployment Guide

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Push your code to GitHub
3. **Environment Variables**: Have your credentials ready

## Step 1: Prepare Your Repository

Ensure these files are in your root directory:
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Deployment command
- ✅ `railway.json` - Railway configuration
- ✅ `runtime.txt` - Python version

## Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository: `vixSPY` (or whatever you named it)

## Step 3: Configure Environment Variables

In Railway dashboard, go to **Variables** and add:

### Required Variables:
```bash
# TradeStation API
TRADESTATION_CLIENT_ID=your_client_id_here
TRADESTATION_CLIENT_SECRET=your_client_secret_here
TRADESTATION_REFRESH_TOKEN=your_refresh_token_here

# Account Configuration
TRADESTATION_SIM_ACCOUNT=SIM2818191M
TRADESTATION_LIVE_ACCOUNT=your_live_account_id

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=postgresql://postgres:password@host:5432/postgres

# Trading Configuration
STRATEGY_ENABLED=false
USE_LIVE_ACCOUNT=false
UNDERLYING_SYMBOL=SPY
DELTA_TARGET=0.3
WING_WIDTH=10
TAKE_PROFIT_PERCENTAGE=0.25

# Schedule (US/Eastern times)
ENTRY_SCHEDULE_HOUR=9
ENTRY_SCHEDULE_MINUTE=32
EXIT_SCHEDULE_HOUR=11
EXIT_SCHEDULE_MINUTE=30

# API Configuration
API_HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO
```

## Step 4: Deploy

1. Railway will automatically detect your Python app
2. It will install dependencies from `requirements.txt`
3. It will run the command from `Procfile`
4. Monitor the **Deploy Logs** for any issues

## Step 5: Verify Deployment

1. **Check Health**: Visit `https://your-app.railway.app/api/health/detailed`
2. **Check API Docs**: Visit `https://your-app.railway.app/docs`
3. **Check Logs**: Monitor for any errors in Railway dashboard

## Step 6: Frontend Deployment (Optional)

If you want to deploy the frontend separately:

1. Create a new Railway project for frontend
2. Set environment variable:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```
3. Deploy from the `frontend/` directory

## Step 7: Enable Strategy

Once everything is deployed and working:

1. **Test in SIM mode first**:
   ```bash
   # Set these in Railway Variables:
   STRATEGY_ENABLED=true
   USE_LIVE_ACCOUNT=false
   ```

2. **Monitor logs** for 24-48 hours

3. **Switch to LIVE** only when confident:
   ```bash
   USE_LIVE_ACCOUNT=true
   ```

## Monitoring Your Deployment

### Railway Dashboard
- Monitor **Metrics** for CPU/Memory usage
- Check **Deploy Logs** for errors
- View **Variables** for configuration

### Your Dashboard
- Visit your Railway URL to see the dashboard
- Monitor VIX conditions and trade decisions
- Check system health and connectivity

### Logs to Watch
- VIX gap detection
- Trading decisions
- Order execution
- PDT compliance checks

## Troubleshooting

### Common Issues:

1. **Build Failures**:
   - Check `requirements.txt` format
   - Verify Python version compatibility

2. **Runtime Errors**:
   - Check all environment variables are set
   - Verify Supabase connection string
   - Check TradeStation API credentials

3. **Timezone Issues**:
   - Scheduler uses US/Eastern automatically
   - Verify schedule times in logs

4. **Database Issues**:
   - Run database setup script first
   - Check Supabase connection

## Cost Optimization

Railway free tier includes:
- $5/month credit
- Should be sufficient for this app

To optimize costs:
- Use single Railway service (backend only)
- Access via Railway's generated URL
- Monitor usage in dashboard

## Security Checklist

- ✅ All secrets in environment variables
- ✅ No credentials in code
- ✅ Supabase RLS configured (if needed)
- ✅ TradeStation API keys secured
- ✅ Database connection encrypted

## Next Steps After Deployment

1. **Monitor for 1 week in SIM mode**
2. **Verify all scheduled jobs work**
3. **Test manual entry/exit buttons**
4. **Verify PDT compliance**
5. **Check performance analytics**
6. **Enable live trading when confident**

Your VIX/SPY Iron Condor strategy will now run 24/7 in the cloud! 🚀