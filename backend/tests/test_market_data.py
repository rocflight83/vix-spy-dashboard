import pytest
from unittest.mock import Mock, patch
from datetime import date, datetime
import pandas as pd
from app.services.market_data import MarketDataService

class TestMarketDataService:
    
    @pytest.fixture
    def service(self, mock_yahoo_ticker):
        """Create MarketDataService with mocked Yahoo Finance"""
        return MarketDataService()
    
    def test_get_vix_data_with_gap_up(self, service, mock_yahoo_ticker):
        """Test VIX data retrieval with gap up condition"""
        # Mock VIX historical data
        mock_data = pd.DataFrame({
            'open': [20.0, 22.5],
            'high': [21.0, 23.0],
            'low': [19.5, 22.0],
            'close': [20.5, 22.8]
        })
        mock_data.index = pd.MultiIndex.from_tuples([
            ('symbol', date(2023, 12, 14)),
            ('symbol', date(2023, 12, 15))
        ])
        
        mock_yahoo_ticker.return_value.history.return_value = mock_data
        
        result = service.get_vix_data()
        
        assert result['current_open'] == 22.5
        assert result['current_high'] == 23.0
        assert result['current_low'] == 22.0
        assert result['current_close'] == 22.8
        assert result['previous_close'] == 20.5
        assert result['gap_amount'] == 2.0  # 22.5 - 20.5
        assert result['gap_percentage'] == pytest.approx(9.756, rel=1e-2)
        assert result['is_gap_up'] == True
    
    def test_get_vix_data_with_gap_down(self, service, mock_yahoo_ticker):
        """Test VIX data retrieval with gap down condition"""
        # Mock VIX historical data with gap down
        mock_data = pd.DataFrame({
            'open': [20.0, 18.5],
            'high': [21.0, 19.0],
            'low': [19.5, 18.0],
            'close': [20.5, 18.8]
        })
        mock_data.index = pd.MultiIndex.from_tuples([
            ('symbol', date(2023, 12, 14)),
            ('symbol', date(2023, 12, 15))
        ])
        
        mock_yahoo_ticker.return_value.history.return_value = mock_data
        
        result = service.get_vix_data()
        
        assert result['current_open'] == 18.5
        assert result['previous_close'] == 20.5
        assert result['gap_amount'] == -2.0  # 18.5 - 20.5
        assert result['gap_percentage'] == pytest.approx(-9.756, rel=1e-2)
        assert result['is_gap_up'] == False
    
    def test_get_vix_data_single_day(self, service, mock_yahoo_ticker):
        """Test VIX data retrieval with only one day of data"""
        # Mock VIX historical data with only one day
        mock_data = pd.DataFrame({
            'open': [20.0],
            'high': [21.0],
            'low': [19.5],
            'close': [20.5]
        })
        mock_data.index = pd.MultiIndex.from_tuples([
            ('symbol', date(2023, 12, 15))
        ])
        
        mock_yahoo_ticker.return_value.history.return_value = mock_data
        
        result = service.get_vix_data()
        
        assert result['current_open'] == 20.0
        assert result['previous_close'] is None
        assert result['gap_amount'] is None
        assert result['gap_percentage'] is None
        assert result['is_gap_up'] == False
    
    def test_get_vix_data_empty(self, service, mock_yahoo_ticker):
        """Test VIX data retrieval with empty data"""
        mock_yahoo_ticker.return_value.history.return_value = pd.DataFrame()
        
        with pytest.raises(Exception, match="No VIX data received"):
            service.get_vix_data()
    
    def test_get_spy_price_success(self, service, mock_yahoo_ticker):
        """Test SPY price retrieval success"""
        # Mock SPY price data
        service.spy_ticker.price = {'SPY': {'regularMarketPrice': 450.25}}
        
        price = service.get_spy_price()
        assert price == 450.25
    
    def test_get_spy_price_fallback_to_history(self, service, mock_yahoo_ticker):
        """Test SPY price retrieval fallback to history"""
        # Mock empty price data, fallback to history
        service.spy_ticker.price = {}
        
        mock_data = pd.DataFrame({
            'close': [451.50]
        })
        service.spy_ticker.history.return_value = mock_data
        
        price = service.get_spy_price()
        assert price == 451.50
    
    def test_get_spy_price_failure(self, service, mock_yahoo_ticker):
        """Test SPY price retrieval failure"""
        service.spy_ticker.price = {}
        service.spy_ticker.history.return_value = pd.DataFrame()
        
        with pytest.raises(Exception, match="Could not fetch SPY price"):
            service.get_spy_price()
    
    @patch('app.services.market_data.SessionLocal')
    def test_store_market_data_new_record(self, mock_session, service):
        """Test storing new market data record"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        data = {
            'date': date(2023, 12, 15),
            'current_open': 22.5,
            'current_high': 23.0,
            'current_low': 22.0,
            'current_close': 22.8,
            'previous_close': 20.5,
            'gap_amount': 2.0,
            'gap_percentage': 9.76
        }
        
        service.store_market_data('^VIX', data)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()
    
    @patch('app.services.market_data.SessionLocal')
    def test_store_market_data_update_existing(self, mock_session, service):
        """Test updating existing market data record"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        existing_record = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_record
        
        data = {
            'date': date(2023, 12, 15),
            'current_open': 22.5,
            'current_high': 23.0,
            'current_low': 22.0,
            'current_close': 22.8,
            'previous_close': 20.5,
            'gap_amount': 2.0,
            'gap_percentage': 9.76
        }
        
        service.store_market_data('^VIX', data)
        
        assert existing_record.open_price == 22.5
        assert existing_record.high_price == 23.0
        assert existing_record.gap_amount == 2.0
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
    
    def test_check_vix_gap_up_condition_success(self, service, mock_yahoo_ticker):
        """Test VIX gap up condition check success"""
        # Mock VIX data with gap up
        mock_data = pd.DataFrame({
            'open': [20.0, 22.5],
            'high': [21.0, 23.0],
            'low': [19.5, 22.0],
            'close': [20.5, 22.8]
        })
        mock_data.index = pd.MultiIndex.from_tuples([
            ('symbol', date(2023, 12, 14)),
            ('symbol', date(2023, 12, 15))
        ])
        
        mock_yahoo_ticker.return_value.history.return_value = mock_data
        
        with patch.object(service, 'store_market_data') as mock_store:
            result = service.check_vix_gap_up_condition()
        
        assert result['vix_gap_up'] == True
        assert result['condition_met'] == True
        assert result['gap_amount'] == 2.0
        assert result['current_vix'] == 22.5
        assert result['previous_vix_close'] == 20.5
        assert 'error' not in result
        
        mock_store.assert_called_once_with('^VIX', {
            'current_open': 22.5,
            'current_high': 23.0,
            'current_low': 22.0,
            'current_close': 22.8,
            'previous_close': 20.5,
            'gap_amount': 2.0,
            'gap_percentage': pytest.approx(9.756, rel=1e-2),
            'is_gap_up': True,
            'date': date.today()
        })
    
    def test_check_vix_gap_up_condition_failure(self, service, mock_yahoo_ticker):
        """Test VIX gap up condition check with error"""
        mock_yahoo_ticker.return_value.history.side_effect = Exception("Yahoo API error")
        
        result = service.check_vix_gap_up_condition()
        
        assert result['vix_gap_up'] == False
        assert result['condition_met'] == False
        assert result['gap_amount'] == 0
        assert result['current_vix'] == 0
        assert 'error' in result
        assert result['error'] == "Yahoo API error"