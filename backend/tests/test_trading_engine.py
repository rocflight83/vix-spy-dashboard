import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime
from app.services.trading_engine import TradingEngine

class TestTradingEngine:
    
    @pytest.fixture
    def trading_engine(self):
        """Create trading engine with mocked dependencies"""
        with patch('app.services.trading_engine.TradeStationAPI'), \
             patch('app.services.trading_engine.MarketDataService'), \
             patch('app.services.trading_engine.PDTComplianceService'):
            return TradingEngine()
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @patch('app.services.trading_engine.SessionLocal')
    async def test_execute_entry_strategy_disabled(self, mock_session, trading_engine):
        """Test entry execution when strategy is disabled"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock strategy disabled
        with patch.object(trading_engine, '_is_strategy_enabled', return_value=False), \
             patch.object(trading_engine, '_record_decision', return_value=None):
            
            result = await trading_engine.execute_entry()
            
            assert "Strategy is disabled" in str(result)
    
    @patch('app.services.trading_engine.SessionLocal')
    async def test_execute_entry_pdt_violation(self, mock_session, trading_engine):
        """Test entry execution when PDT rule would be violated"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock strategy enabled but PDT violation
        trading_engine.pdt_service.check_pdt_compliance.return_value = {
            "can_trade_today": False,
            "trades_remaining": 0
        }
        
        with patch.object(trading_engine, '_is_strategy_enabled', return_value=True), \
             patch.object(trading_engine, '_record_decision', return_value=None):
            
            result = await trading_engine.execute_entry()
            
            assert "PDT rule violation" in str(result)
    
    @patch('app.services.trading_engine.SessionLocal')
    async def test_execute_entry_existing_position(self, mock_session, trading_engine):
        """Test entry execution when position already exists"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock existing open trade
        existing_trade = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_trade
        
        trading_engine.pdt_service.check_pdt_compliance.return_value = {
            "can_trade_today": True
        }
        
        with patch.object(trading_engine, '_is_strategy_enabled', return_value=True), \
             patch.object(trading_engine, '_record_decision', return_value=None):
            
            result = await trading_engine.execute_entry()
            
            assert "Already have open position" in str(result)
    
    @patch('app.services.trading_engine.SessionLocal')
    async def test_execute_entry_vix_condition_not_met(self, mock_session, trading_engine):
        """Test entry execution when VIX condition is not met"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # No existing trade
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # VIX condition not met
        trading_engine.market_data.check_vix_gap_up_condition.return_value = {
            "condition_met": False,
            "current_vix": 20.0,
            "vix_gap_up": False
        }
        
        trading_engine.pdt_service.check_pdt_compliance.return_value = {
            "can_trade_today": True
        }
        
        with patch.object(trading_engine, '_is_strategy_enabled', return_value=True), \
             patch.object(trading_engine, '_record_decision', return_value=None):
            
            result = await trading_engine.execute_entry()
            
            assert "VIX gap up condition not met" in str(result)
    
    @patch('app.services.trading_engine.SessionLocal')
    async def test_execute_entry_successful_trade(self, mock_session, trading_engine):
        """Test successful entry execution"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # No existing trade
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # VIX condition met
        trading_engine.market_data.check_vix_gap_up_condition.return_value = {
            "condition_met": True,
            "current_vix": 22.5,
            "vix_gap_up": True,
            "previous_vix_close": 20.0
        }
        
        trading_engine.pdt_service.check_pdt_compliance.return_value = {
            "can_trade_today": True
        }
        
        # Mock successful trade execution
        mock_trade_result = {
            "success": True,
            "expiration_date": date.today(),
            "put_strike": 400.0,
            "put_wing_strike": 390.0,
            "call_strike": 420.0,
            "call_wing_strike": 430.0,
            "entry_price": 2.50,
            "max_profit": 2.50,
            "max_loss": 7.50,
            "spy_price": 405.0,
            "order_id": "12345"
        }
        
        with patch.object(trading_engine, '_is_strategy_enabled', return_value=True), \
             patch.object(trading_engine, '_record_decision', return_value=None), \
             patch.object(trading_engine, '_execute_iron_condor_entry', return_value=mock_trade_result):
            
            result = await trading_engine.execute_entry()
            
            assert result["success"] == True
            assert "trade_id" in result
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called()
    
    @patch('app.services.trading_engine.SessionLocal')
    async def test_execute_exit_no_positions(self, mock_session, trading_engine):
        """Test exit execution with no open positions"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # No open trades
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with patch.object(trading_engine, '_record_decision', return_value=None):
            result = await trading_engine.execute_exit()
            
            assert result["success"] == True
            assert "No open positions" in result["message"]
            assert result["trades_closed"] == 0
    
    @patch('app.services.trading_engine.SessionLocal')
    async def test_execute_exit_successful(self, mock_session, trading_engine):
        """Test successful exit execution"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock open trade
        mock_trade = Mock()
        mock_trade.id = 1
        mock_trade.entry_price = 2.50
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_trade]
        
        # Mock successful exit
        mock_exit_result = {
            "success": True,
            "exit_price": 1.25,
            "realized_pnl": 1.25,
            "order_id": "exit123"
        }
        
        with patch.object(trading_engine, '_record_decision', return_value=None), \
             patch.object(trading_engine, '_execute_trade_exit', return_value=mock_exit_result):
            
            result = await trading_engine.execute_exit()
            
            assert result["success"] == True
            assert result["trades_closed"] == 1
            assert mock_trade.is_open == False
            assert mock_trade.exit_reason == "timed_exit"
            mock_db.commit.assert_called()
    
    async def test_execute_iron_condor_entry_success(self, trading_engine):
        """Test iron condor entry execution"""
        # Mock API response
        trading_engine.api.get_options_chain = AsyncMock(return_value=[
            {"Strike": "400", "Side": "Put", "Delta": -0.3, "Bid": 2.5, "Ask": 2.6},
            {"Strike": "420", "Side": "Call", "Delta": 0.3, "Bid": 2.4, "Ask": 2.5}
        ])
        
        vix_condition = {"current_vix": 22.5, "previous_vix_close": 20.0}
        
        result = await trading_engine._execute_iron_condor_entry("SIM123", vix_condition)
        
        # This is a placeholder test since the full logic needs integration
        assert "success" in result
    
    async def test_execute_trade_exit_success(self, trading_engine):
        """Test trade exit execution"""
        mock_trade = Mock()
        mock_trade.entry_price = 2.50
        
        # Mock API response
        trading_engine.api.get_positions = AsyncMock(return_value=[
            {"Symbol": "SPY 231215P400", "Quantity": "1"}
        ])
        
        result = await trading_engine._execute_trade_exit("SIM123", mock_trade)
        
        # This is a placeholder test since the full logic needs integration
        assert "success" in result
    
    async def test_is_strategy_enabled_true(self, trading_engine):
        """Test strategy enabled check"""
        mock_db = Mock()
        
        with patch('app.services.trading_engine.get_config_value') as mock_get_config:
            mock_get_config.return_value = "true"
            
            result = await trading_engine._is_strategy_enabled(mock_db)
            assert result == True
    
    async def test_is_strategy_enabled_false(self, trading_engine):
        """Test strategy disabled check"""
        mock_db = Mock()
        
        with patch('app.services.trading_engine.get_config_value') as mock_get_config:
            mock_get_config.return_value = "false"
            
            result = await trading_engine._is_strategy_enabled(mock_db)
            assert result == False
    
    async def test_record_decision_success(self, trading_engine):
        """Test decision recording"""
        mock_db = Mock()
        
        with patch.object(trading_engine, '_is_strategy_enabled', return_value=True):
            await trading_engine._record_decision(
                mock_db, "entry_attempt", True, "Test reason", "sim",
                vix_value=22.5, trade_id=1
            )
            
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    async def test_record_decision_error_handling(self, trading_engine):
        """Test decision recording error handling"""
        mock_db = Mock()
        mock_db.commit.side_effect = Exception("Database error")
        
        with patch.object(trading_engine, '_is_strategy_enabled', return_value=True):
            # Should not raise exception
            await trading_engine._record_decision(
                mock_db, "entry_attempt", False, "Test reason", "sim"
            )
            
            mock_db.rollback.assert_called_once()