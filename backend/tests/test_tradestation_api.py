import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from app.services.tradestation_api import TradeStationAPI, TradeStationAPIError

@pytest.mark.asyncio
class TestTradeStationAPI:
    
    @pytest.fixture
    def api(self, test_settings):
        """Create TradeStation API instance with test settings"""
        with patch('app.services.tradestation_api.settings', test_settings):
            return TradeStationAPI()
    
    async def test_get_access_token_success(self, api, mock_httpx_client):
        """Test successful token retrieval"""
        # Mock successful token response
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'expires_in': 3600
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        token = await api.get_access_token()
        
        assert token == 'test_access_token'
        assert api.access_token == 'test_access_token'
        assert api.token_expiry is not None
        
        # Verify API call was made with correct parameters
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert 'signin.tradestation.com' in call_args[0][0]
        assert call_args[1]['data']['grant_type'] == 'refresh_token'
    
    async def test_get_access_token_cached(self, api):
        """Test that cached token is returned when not expired"""
        # Set up cached token
        api.access_token = 'cached_token'
        api.token_expiry = datetime.now() + timedelta(minutes=30)
        
        token = await api.get_access_token()
        
        assert token == 'cached_token'
    
    async def test_get_access_token_force_refresh(self, api, mock_httpx_client):
        """Test force refresh of token"""
        # Set up cached token
        api.access_token = 'cached_token'
        api.token_expiry = datetime.now() + timedelta(minutes=30)
        
        # Mock new token response
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'expires_in': 3600
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        token = await api.get_access_token(force_refresh=True)
        
        assert token == 'new_access_token'
        assert api.access_token == 'new_access_token'
    
    async def test_get_access_token_failure(self, api, mock_httpx_client):
        """Test token retrieval failure"""
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(side_effect=Exception("Network error"))
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        with pytest.raises(TradeStationAPIError):
            await api.get_access_token()
    
    async def test_make_request_success(self, api, mock_httpx_client):
        """Test successful API request"""
        api.access_token = 'valid_token'
        api.token_expiry = datetime.now() + timedelta(minutes=30)
        
        mock_response = Mock()
        mock_response.json.return_value = {'data': 'test_data'}
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await api._make_request('GET', '/test-endpoint')
        
        assert result == {'data': 'test_data'}
        mock_client_instance.request.assert_called_once()
    
    async def test_make_request_with_token_refresh(self, api, mock_httpx_client):
        """Test API request that requires token refresh"""
        api.access_token = None
        
        # Mock token refresh
        mock_token_response = Mock()
        mock_token_response.json.return_value = {
            'access_token': 'new_token',
            'expires_in': 3600
        }
        mock_token_response.raise_for_status = Mock()
        
        # Mock actual API request
        mock_api_response = Mock()
        mock_api_response.json.return_value = {'data': 'test_data'}
        mock_api_response.headers = {'content-type': 'application/json'}
        mock_api_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_client_instance.request = AsyncMock(return_value=mock_api_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await api._make_request('GET', '/test-endpoint')
        
        assert result == {'data': 'test_data'}
        assert api.access_token == 'new_token'
    
    async def test_get_options_chain(self, api, mock_httpx_client):
        """Test options chain retrieval"""
        api.access_token = 'valid_token'
        api.token_expiry = datetime.now() + timedelta(minutes=30)
        
        # Mock streaming response
        mock_response = AsyncMock()
        mock_response.aiter_lines = AsyncMock(return_value=[
            '{"Strikes":["400"],"Side":"Put","Delta":-0.3,"Bid":2.50,"Ask":2.55}',
            '{"Strikes":["405"],"Side":"Put","Delta":-0.25,"Bid":3.00,"Ask":3.05}',
            '{"Strikes":["410"],"Side":"Call","Delta":0.25,"Bid":2.75,"Ask":2.80}'
        ])
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.stream = AsyncMock()
        mock_client_instance.stream.return_value.__aenter__.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        chain = await api.get_options_chain('SPY', '12-15-2023')
        
        assert len(chain) == 3
        assert chain[0]['Strike'] == '400'
        assert chain[0]['Side'] == 'Put'
        assert chain[0]['Delta'] == -0.3
        assert chain[0]['Mid'] == '2.525'
    
    async def test_place_order(self, api, mock_httpx_client):
        """Test order placement"""
        api.access_token = 'valid_token'
        api.token_expiry = datetime.now() + timedelta(minutes=30)
        
        mock_response = Mock()
        mock_response.json.return_value = {'OrderID': '12345', 'Status': 'Received'}
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        order_payload = {
            'AccountID': 'TEST123456',
            'OrderType': 'Market',
            'Legs': [{'Symbol': 'SPY 231215P400', 'Quantity': 1, 'TradeAction': 'BUYTOOPEN'}]
        }
        
        result = await api.place_order(order_payload)
        
        assert result['OrderID'] == '12345'
        assert result['Status'] == 'Received'
    
    async def test_get_orders(self, api, mock_httpx_client):
        """Test getting orders"""
        api.access_token = 'valid_token'
        api.token_expiry = datetime.now() + timedelta(minutes=30)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'Orders': [
                {'OrderID': '12345', 'Status': 'Filled'},
                {'OrderID': '12346', 'Status': 'Received'}
            ]
        }
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        orders = await api.get_orders('TEST123456')
        
        assert len(orders) == 2
        assert orders[0]['OrderID'] == '12345'
        assert orders[1]['Status'] == 'Received'
    
    async def test_get_positions(self, api, mock_httpx_client):
        """Test getting positions"""
        api.access_token = 'valid_token'
        api.token_expiry = datetime.now() + timedelta(minutes=30)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'Positions': [
                {'Symbol': 'SPY 231215P400', 'Quantity': '1', 'LongShort': 'Long'},
                {'Symbol': 'SPY 231215P410', 'Quantity': '-1', 'LongShort': 'Short'}
            ]
        }
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        positions = await api.get_positions('TEST123456')
        
        assert len(positions) == 2
        assert positions[0]['Symbol'] == 'SPY 231215P400'
        assert positions[1]['LongShort'] == 'Short'