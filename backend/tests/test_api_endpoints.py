import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import date
from fastapi.testclient import TestClient

class TestHealthEndpoints:
    
    def test_basic_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get("/api/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "VIX/SPY Trading Dashboard"
    
    def test_scheduler_status(self, client):
        """Test scheduler status endpoint"""
        with patch('app.core.scheduler.scheduler') as mock_scheduler:
            mock_scheduler.scheduler.running = True
            mock_scheduler.get_next_run_times.return_value = {
                "entry_job": {"next_run": "2023-12-15T09:32:00"},
                "exit_job": {"next_run": "2023-12-15T11:30:00"}
            }
            mock_scheduler.is_trading_day.return_value = True
            mock_scheduler.scheduler.timezone = "US/Eastern"
            
            response = client.get("/api/health/scheduler")
            
            assert response.status_code == 200
            data = response.json()
            assert data["running"] == True
            assert data["is_trading_day"] == True
            assert "next_runs" in data

class TestTradeEndpoints:
    
    def test_get_trades_empty(self, client):
        """Test getting trades when none exist"""
        response = client.get("/api/trades/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_current_position_none(self, client):
        """Test getting current position when none exists"""
        response = client.get("/api/trades/current/position")
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_position"] == False
        assert data["trade"] is None
        assert "No current position" in data["message"]
    
    def test_get_trade_decisions_empty(self, client):
        """Test getting trade decisions when none exist"""
        response = client.get("/api/trades/decisions/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

class TestStrategyEndpoints:
    
    def test_get_strategy_status(self, client):
        """Test getting strategy status"""
        with patch('app.routers.strategy.get_config_value') as mock_get_config, \
             patch('app.core.scheduler.scheduler') as mock_scheduler:
            
            mock_get_config.side_effect = lambda db, key, default: {
                'strategy_enabled': 'false',
                'use_live_account': 'false'
            }.get(key, default)
            
            mock_scheduler.get_next_run_times.return_value = {
                "entry_job": {"next_run": "2023-12-15T09:32:00"},
                "exit_job": {"next_run": "2023-12-15T11:30:00"}
            }
            mock_scheduler.is_trading_day.return_value = True
            mock_scheduler.scheduler.running = True
            
            response = client.get("/api/strategy/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["strategy_enabled"] == False
            assert data["use_live_account"] == False
            assert data["is_trading_day"] == True
            assert data["scheduler_running"] == True
    
    def test_toggle_strategy(self, client):
        """Test toggling strategy on/off"""
        with patch('app.routers.strategy.set_config_value') as mock_set_config, \
             patch('app.core.scheduler.scheduler') as mock_scheduler:
            
            mock_set_config.return_value = None
            mock_scheduler.resume_jobs = Mock()
            
            response = client.post("/api/strategy/toggle?enabled=true")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["strategy_enabled"] == True
            assert "enabled" in data["message"]
            mock_scheduler.resume_jobs.assert_called_once()
    
    def test_toggle_account_type(self, client):
        """Test toggling account type"""
        with patch('app.routers.strategy.set_config_value') as mock_set_config, \
             patch('app.core.config.settings') as mock_settings:
            
            mock_set_config.return_value = None
            mock_settings.get_account_id.return_value = "LIVE123456"
            
            response = client.post("/api/strategy/account/toggle?use_live=true")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["use_live_account"] == True
            assert data["account_type"] == "live"
    
    def test_get_config_empty(self, client):
        """Test getting configuration when empty"""
        response = client.get("/api/strategy/config")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

class TestAnalyticsEndpoints:
    
    def test_get_performance_metrics_no_trades(self, client):
        """Test getting performance metrics when no trades exist"""
        response = client.get("/api/analytics/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 0
        assert data["winning_trades"] == 0
        assert data["losing_trades"] == 0
        assert data["win_rate"] == 0.0
        assert data["total_pnl"] == 0.0
    
    def test_get_pnl_chart_data_empty(self, client):
        """Test getting P&L chart data when no trades exist"""
        response = client.get("/api/analytics/chart/pnl")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["labels"], list)
        assert isinstance(data["values"], list)
        assert data["chart_type"] == "cumulative"
        assert len(data["labels"]) > 0  # Should have date range even if no trades
    
    def test_get_pdt_status(self, client):
        """Test getting PDT status"""
        response = client.get("/api/analytics/pdt-status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_day_trades"] == 0
        assert data["max_allowed_trades"] == 3
        assert data["trades_remaining"] == 3
        assert data["is_compliant"] == True
        assert data["violation_risk"] == False
        assert isinstance(data["recent_records"], list)
    
    def test_get_market_conditions_empty(self, client):
        """Test getting market conditions when no data exists"""
        response = client.get("/api/analytics/market-conditions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # No market data stored yet

class TestEndpointErrorHandling:
    
    def test_get_nonexistent_trade(self, client):
        """Test getting a trade that doesn't exist"""
        response = client.get("/api/trades/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_invalid_parameters(self, client):
        """Test endpoints with invalid parameters"""
        # Test with invalid limit
        response = client.get("/api/trades/?limit=1000")  # Exceeds max limit
        
        assert response.status_code == 422  # Validation error
    
    def test_strategy_toggle_error_handling(self, client):
        """Test strategy toggle error handling"""
        with patch('app.routers.strategy.set_config_value') as mock_set_config:
            mock_set_config.side_effect = Exception("Database error")
            
            response = client.post("/api/strategy/toggle?enabled=true")
            
            assert response.status_code == 500
            data = response.json()
            assert "Database error" in data["detail"]

class TestEndpointParameterValidation:
    
    def test_trades_query_parameters(self, client):
        """Test trade endpoint query parameter validation"""
        # Test with valid parameters
        response = client.get("/api/trades/?limit=10&offset=0&account_type=sim")
        assert response.status_code == 200
        
        # Test with date parameters
        response = client.get("/api/trades/?start_date=2023-12-01&end_date=2023-12-31")
        assert response.status_code == 200
    
    def test_analytics_parameters(self, client):
        """Test analytics endpoint parameter validation"""
        # Test performance metrics with date range
        response = client.get("/api/analytics/performance?start_date=2023-12-01&end_date=2023-12-31&account_type=sim")
        assert response.status_code == 200
        
        # Test chart data parameters
        response = client.get("/api/analytics/chart/pnl?chart_type=daily")
        assert response.status_code == 200
        
        response = client.get("/api/analytics/chart/pnl?chart_type=cumulative")
        assert response.status_code == 200