# Supabase Database Setup Guide

This guide will help you set up the Supabase database for the VIX/SPY Iron Condor Trading Dashboard.

## Prerequisites

- Supabase account (sign up at [supabase.com](https://supabase.com))
- Basic understanding of SQL and PostgreSQL

## Step 1: Create a New Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Choose your organization
4. Fill in project details:
   - **Name**: `vix-spy-trading-dashboard`
   - **Database Password**: Choose a strong password and save it securely
   - **Region**: Choose the region closest to your deployment location
5. Click "Create new project"
6. Wait for the project to be fully initialized (2-3 minutes)

## Step 2: Get Your Project Credentials

Once your project is created:

1. Go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (e.g., `https://your-project-id.supabase.co`)
   - **Project API Keys** → **anon public**
   - **Project API Keys** → **service_role** (keep this secret!)

3. Go to **Settings** → **Database**
4. Copy the **Connection string** → **Pooler** → **Connection pooling**
   - Choose "Transaction" mode
   - Copy the PostgreSQL connection string

## Step 3: Update Environment Variables

Update your `backend/.env` file with the Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres.your-project-id:your-db-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true&connection_limit=1
```

## Step 4: Create Database Tables

### Option A: Using the SQL Editor (Recommended)

1. In your Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Copy the entire contents of `database_setup.sql`
4. Paste it into the SQL editor
5. Click "Run" to execute the script

### Option B: Using Alembic (for development)

If you prefer using migrations for development:

```bash
cd backend
pip install alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Step 5: Verify Database Setup

1. Go to **Table Editor** in your Supabase dashboard
2. You should see the following tables:
   - `trades` - Trade execution records
   - `pdt_tracking` - Pattern day trading compliance
   - `strategy_config` - Application configuration
   - `trade_decisions` - Audit trail of decisions
   - `market_data` - VIX and SPY data storage

3. Check that the default configuration values are inserted in `strategy_config`

## Step 6: Test Database Connection

To test your database connection, run the FastAPI application:

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/api/health/detailed` to check if the database connection is working.

## Database Schema Overview

### Tables and Their Purposes

- **trades**: Stores all iron condor trade records with entry/exit details, P&L, and order IDs
- **pdt_tracking**: Tracks day trading activity to ensure PDT rule compliance
- **strategy_config**: Stores application configuration (strategy on/off, account type, etc.)
- **trade_decisions**: Audit trail of every trading decision made by the system
- **market_data**: Historical VIX and SPY data for analysis and backtesting

### Key Features

- **Automatic timestamps** with triggers for `updated_at` fields
- **Indexes** for optimal query performance
- **Foreign key relationships** for data integrity
- **Default values** for common configuration

## Security Considerations

1. **Never commit your `.env` file** - it contains sensitive database credentials
2. **Use service role key only on the backend** - never expose it to frontend
3. **Consider enabling Row Level Security (RLS)** for production multi-user scenarios
4. **Regularly rotate your database password** and API keys

## Backup and Maintenance

- Supabase automatically creates backups, but consider setting up additional backup strategies for production
- Monitor database size and performance in the Supabase dashboard
- Review and clean up old trade data periodically to manage storage

## Troubleshooting

### Connection Issues
- Verify the DATABASE_URL format matches your Supabase connection string
- Ensure you're using the "Transaction" mode pooler URL
- Check that your project is not paused (free tier limitation)

### Permission Errors
- Verify you're using the correct service role key for backend operations
- Ensure the database user has necessary permissions

### Migration Issues
- If using Alembic, ensure your models match the database schema
- For schema changes, always test migrations on a development database first

## Next Steps

Once your database is set up:
1. Update your `.env` file with the correct credentials
2. Test the API endpoints to ensure database connectivity
3. Set up your TradeStation API credentials
4. Configure the trading strategy parameters in the `strategy_config` table