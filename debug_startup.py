#!/usr/bin/env python3
"""
Debug script to identify startup issues
"""
import os
import sys

print("=== ENVIRONMENT DEBUG ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

print("\n=== CHECKING IMPORTS ===")
try:
    from fastapi import FastAPI
    print("✓ FastAPI import OK")
except Exception as e:
    print(f"✗ FastAPI import failed: {e}")

try:
    from pydantic_settings import BaseSettings
    print("✓ Pydantic settings import OK")
except Exception as e:
    print(f"✗ Pydantic settings import failed: {e}")

print("\n=== CHECKING ENVIRONMENT VARIABLES ===")
required_vars = [
    "TRADESTATION_CLIENT_ID",
    "TRADESTATION_CLIENT_SECRET", 
    "TRADESTATION_REFRESH_TOKEN",
    "SUPABASE_URL",
    "DATABASE_URL"
]

optional_vars = [
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY"
]

for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✓ {var} = {value[:10]}...")
    else:
        print(f"✗ {var} = MISSING")

for var in optional_vars:
    value = os.getenv(var)
    if value:
        print(f"? {var} = {value[:10]}...")
    else:
        print(f"? {var} = Not set (optional)")

print("\n=== CHECKING CONFIG ===")
try:
    sys.path.append('/app/backend')
    from app.core.config import settings
    print("✓ Config loaded successfully")
    print(f"  Strategy enabled: {settings.STRATEGY_ENABLED}")
    print(f"  Use live account: {settings.USE_LIVE_ACCOUNT}")
except Exception as e:
    print(f"✗ Config failed: {e}")

print("\n=== CHECKING DATABASE ===")
try:
    import asyncpg
    print("✓ asyncpg import OK")
except Exception as e:
    print(f"✗ asyncpg import failed: {e}")

print("\n=== CHECKING SCHEDULER ===")
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    print("✓ APScheduler import OK")
except Exception as e:
    print(f"✗ APScheduler import failed: {e}")