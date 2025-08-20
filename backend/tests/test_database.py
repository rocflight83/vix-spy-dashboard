import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models.database import Trade, PDTTracking, StrategyConfig, TradeDecision, MarketData

class TestDatabaseModels:
    
    def test_trade_model_creation(self, test_db):
        """Test Trade model creation and basic operations"""
        db_gen = test_db()
        db = next(db_gen)
        
        trade = Trade(
            trade_date=date(2023, 12, 15),
            underlying_symbol='SPY',
            expiration_date=date(2023, 12, 15),
            put_strike=400.0,
            put_wing_strike=390.0,
            call_strike=410.0,
            call_wing_strike=420.0,
            quantity=1,
            entry_price=2.50,
            max_profit=2.50,
            max_loss=7.50,
            account_type='sim',
            vix_open=22.5,
            vix_previous_close=20.5,
            spy_price_at_entry=405.0
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        assert trade.id is not None
        assert trade.trade_date == date(2023, 12, 15)
        assert trade.underlying_symbol == 'SPY'
        assert trade.is_open == True  # Default value
        assert trade.created_at is not None
        assert trade.updated_at is not None
    
    def test_trade_model_relationships(self, test_db):
        """Test Trade model with calculated fields"""
        db_gen = test_db()
        db = next(db_gen)
        
        trade = Trade(
            trade_date=date.today(),
            underlying_symbol='SPY',
            expiration_date=date.today(),
            put_strike=400.0,
            put_wing_strike=390.0,
            call_strike=410.0,
            call_wing_strike=420.0,
            quantity=1,
            entry_price=2.50,
            exit_price=1.25,
            max_profit=2.50,
            max_loss=7.50,
            account_type='sim',
            is_open=False,
            exit_reason='take_profit'
        )
        
        # Calculate realized P&L
        trade.realized_pnl = trade.entry_price - trade.exit_price  # Credit spread
        
        db.add(trade)
        db.commit()
        
        assert trade.realized_pnl == 1.25
        assert trade.is_open == False
        assert trade.exit_reason == 'take_profit'
    
    def test_pdt_tracking_model(self, test_db):
        """Test PDTTracking model"""
        db_gen = test_db()
        db = next(db_gen)
        
        pdt_record = PDTTracking(
            trade_date=date.today(),
            account_type='sim',
            trade_count=1,
            is_pdt_violation=False
        )
        
        db.add(pdt_record)
        db.commit()
        db.refresh(pdt_record)
        
        assert pdt_record.id is not None
        assert pdt_record.trade_count == 1
        assert pdt_record.is_pdt_violation == False
        assert pdt_record.created_at is not None
    
    def test_strategy_config_model(self, test_db):
        """Test StrategyConfig model"""
        db_gen = test_db()
        db = next(db_gen)
        
        config = StrategyConfig(
            config_key='strategy_enabled',
            config_value='false',
            description='Whether the strategy is enabled'
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        assert config.id is not None
        assert config.config_key == 'strategy_enabled'
        assert config.config_value == 'false'
        assert config.updated_at is not None
    
    def test_strategy_config_unique_constraint(self, test_db):
        """Test that config_key must be unique"""
        db_gen = test_db()
        db = next(db_gen)
        
        config1 = StrategyConfig(
            config_key='test_key',
            config_value='value1'
        )
        
        config2 = StrategyConfig(
            config_key='test_key',  # Same key
            config_value='value2'
        )
        
        db.add(config1)
        db.commit()
        
        db.add(config2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db.commit()
    
    def test_trade_decision_model(self, test_db):
        """Test TradeDecision model"""
        db_gen = test_db()
        db = next(db_gen)
        
        # First create a trade
        trade = Trade(
            trade_date=date.today(),
            underlying_symbol='SPY',
            expiration_date=date.today(),
            put_strike=400.0,
            put_wing_strike=390.0,
            call_strike=410.0,
            call_wing_strike=420.0,
            account_type='sim'
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        # Create a trade decision linked to the trade
        decision = TradeDecision(
            decision_type='entry_attempt',
            action_taken=True,
            reason='VIX gap up detected',
            vix_value=22.5,
            vix_gap_up=True,
            spy_price=405.0,
            account_type='sim',
            pdt_trades_remaining=2,
            strategy_enabled=True,
            trade_id=trade.id
        )
        
        db.add(decision)
        db.commit()
        db.refresh(decision)
        
        assert decision.id is not None
        assert decision.action_taken == True
        assert decision.reason == 'VIX gap up detected'
        assert decision.trade_id == trade.id
        assert decision.created_at is not None
    
    def test_market_data_model(self, test_db):
        """Test MarketData model"""
        db_gen = test_db()
        db = next(db_gen)
        
        market_data = MarketData(
            data_date=date.today(),
            symbol='^VIX',
            open_price=22.5,
            high_price=23.0,
            low_price=22.0,
            close_price=22.8,
            previous_close=20.5,
            gap_amount=2.0,
            gap_percentage=9.76
        )
        
        db.add(market_data)
        db.commit()
        db.refresh(market_data)
        
        assert market_data.id is not None
        assert market_data.symbol == '^VIX'
        assert market_data.gap_amount == 2.0
        assert market_data.created_at is not None
    
    def test_market_data_unique_constraint(self, test_db):
        """Test that data_date + symbol must be unique"""
        db_gen = test_db()
        db = next(db_gen)
        
        data1 = MarketData(
            data_date=date.today(),
            symbol='^VIX',
            open_price=22.5,
            high_price=23.0,
            low_price=22.0,
            close_price=22.8
        )
        
        data2 = MarketData(
            data_date=date.today(),  # Same date
            symbol='^VIX',           # Same symbol
            open_price=23.0,
            high_price=23.5,
            low_price=22.5,
            close_price=23.2
        )
        
        db.add(data1)
        db.commit()
        
        db.add(data2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db.commit()
    
    def test_query_operations(self, test_db):
        """Test basic query operations"""
        db_gen = test_db()
        db = next(db_gen)
        
        # Create test data
        trade1 = Trade(
            trade_date=date.today(),
            underlying_symbol='SPY',
            expiration_date=date.today(),
            put_strike=400.0,
            put_wing_strike=390.0,
            call_strike=410.0,
            call_wing_strike=420.0,
            account_type='sim',
            is_open=True
        )
        
        trade2 = Trade(
            trade_date=date.today(),
            underlying_symbol='SPY',
            expiration_date=date.today(),
            put_strike=405.0,
            put_wing_strike=395.0,
            call_strike=415.0,
            call_wing_strike=425.0,
            account_type='live',
            is_open=False,
            realized_pnl=1.50
        )
        
        db.add_all([trade1, trade2])
        db.commit()
        
        # Test queries
        all_trades = db.query(Trade).all()
        assert len(all_trades) == 2
        
        open_trades = db.query(Trade).filter(Trade.is_open == True).all()
        assert len(open_trades) == 1
        assert open_trades[0].account_type == 'sim'
        
        live_trades = db.query(Trade).filter(Trade.account_type == 'live').all()
        assert len(live_trades) == 1
        assert live_trades[0].realized_pnl == 1.50
        
        closed_profitable = db.query(Trade).filter(
            Trade.is_open == False,
            Trade.realized_pnl > 0
        ).all()
        assert len(closed_profitable) == 1