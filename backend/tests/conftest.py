import pytest
import asyncio
from typing import Generator
from unittest.mock import Mock, patch
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, get_db
from app.core.config import Settings
from fastapi.testclient import TestClient

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_settings():
    """Create test settings with mock values"""
    return Settings(
        TRADESTATION_CLIENT_ID="test_client_id",
        TRADESTATION_CLIENT_SECRET="test_client_secret",
        TRADESTATION_REFRESH_TOKEN="test_refresh_token",
        TRADESTATION_SIM_ACCOUNT="TEST123456",
        TRADESTATION_LIVE_ACCOUNT="LIVE123456",
        SUPABASE_URL="http://localhost:54321",
        SUPABASE_ANON_KEY="test_anon_key",
        SUPABASE_SERVICE_ROLE_KEY="test_service_role_key",
        DATABASE_URL=TEST_DATABASE_URL,
        STRATEGY_ENABLED=False,
        USE_LIVE_ACCOUNT=False,
        VIX_SYMBOL="^VIX",
        UNDERLYING_SYMBOL="SPY",
        DELTA_TARGET=0.3,
        WING_WIDTH=10,
        TAKE_PROFIT_PERCENTAGE=0.25,
        ENTRY_SCHEDULE_HOUR=9,
        ENTRY_SCHEDULE_MINUTE=32,
        EXIT_SCHEDULE_HOUR=11,
        EXIT_SCHEDULE_MINUTE=30
    )

@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    yield override_get_db
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
def client(test_db, test_settings):
    """Create a test client with dependency overrides"""
    from app.main import app
    
    # Override dependencies
    app.dependency_overrides[get_db] = test_db
    
    with patch('app.core.config.settings', test_settings):
        with TestClient(app) as client:
            yield client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API testing"""
    with patch('httpx.AsyncClient') as mock_client:
        yield mock_client

@pytest.fixture
def mock_yahoo_ticker():
    """Mock Yahoo Finance ticker for market data testing"""
    with patch('yahooquery.Ticker') as mock_ticker:
        yield mock_ticker