import httpx
import json
import logging
import math
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

class TradeStationAPIError(Exception):
    """Custom exception for TradeStation API errors"""
    pass

class TradeStationAPI:
    def __init__(self):
        self.client_id = settings.TRADESTATION_CLIENT_ID
        self.client_secret = settings.TRADESTATION_CLIENT_SECRET  
        self.refresh_token = settings.TRADESTATION_REFRESH_TOKEN
        self.base_url = settings.get_tradestation_base_url()
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """Get or refresh access token"""
        if self.access_token and not force_refresh and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token
        
        url = "https://signin.tradestation.com/oauth/token"
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, headers=headers)
                response.raise_for_status()
                
                token_data = response.json()
                self.access_token = token_data['access_token']
                
                # Set expiry to 80% of actual expiry for safety
                expires_in = token_data.get('expires_in', 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in * 0.8)
                
                logger.info("Successfully refreshed TradeStation access token")
                return self.access_token
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting access token: {e}")
            raise TradeStationAPIError(f"Failed to get access token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting access token: {e}")
            raise TradeStationAPIError(f"Unexpected error: {e}")
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        stream: bool = False
    ) -> Any:
        """Make authenticated request to TradeStation API"""
        token = await self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if stream:
                    # For streaming responses (like options chains)
                    async with client.stream(method, url, headers=headers, params=params) as response:
                        response.raise_for_status()
                        return response
                else:
                    response = await client.request(
                        method, url, headers=headers, params=params, json=json_data
                    )
                    response.raise_for_status()
                    
                    if response.headers.get('content-type', '').startswith('application/json'):
                        return response.json()
                    return response.text
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in API request: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            raise TradeStationAPIError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            raise TradeStationAPIError(f"Unexpected error: {e}")
    
    async def get_options_chain(
        self, 
        symbol: str, 
        expiration: str,
        strike_proximity: int = 20
    ) -> List[Dict[str, Any]]:
        """Get options chain data for a symbol"""
        endpoint = f"/v3/marketdata/stream/options/chains/{symbol}"
        
        params = {
            "expiration": expiration,
            "strikeProximity": str(strike_proximity),
        }
        
        try:
            chain_data = []
            response = await self._make_request("GET", endpoint, params=params, stream=True)
            
            i = 1
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chain_data.append({
                            'Strike': data['Strikes'][0],
                            'Side': data['Side'],
                            'Delta': data['Delta'],
                            'Bid': data['Bid'],
                            'Ask': data['Ask'],
                            'Mid': str((float(data['Ask']) + float(data['Bid'])) / 2)
                        })
                        i += 1
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Error parsing options data: {e}")
                        continue
                    
                if i > strike_proximity * 4:
                    break
            
            return chain_data
            
        except Exception as e:
            logger.error(f"Error getting options chain: {e}")
            raise TradeStationAPIError(f"Failed to get options chain: {e}")
    
    async def place_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Place an order"""
        endpoint = "/v3/orderexecution/orders"
        
        try:
            response = await self._make_request("POST", endpoint, json_data=order_payload)
            logger.info(f"Order placed successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise TradeStationAPIError(f"Failed to place order: {e}")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        endpoint = f"/v3/orderexecution/orders/{order_id}"
        
        try:
            response = await self._make_request("DELETE", endpoint)
            logger.info(f"Order cancelled successfully: {order_id}")
            return response
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            raise TradeStationAPIError(f"Failed to cancel order: {e}")
    
    async def get_orders(self, account_id: str) -> List[Dict[str, Any]]:
        """Get orders for an account"""
        endpoint = f"/v3/brokerage/accounts/{account_id}/orders"
        
        try:
            response = await self._make_request("GET", endpoint)
            return response.get('Orders', [])
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            raise TradeStationAPIError(f"Failed to get orders: {e}")
    
    async def get_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """Get positions for an account"""
        endpoint = f"/v3/brokerage/accounts/{account_id}/positions"
        
        try:
            response = await self._make_request("GET", endpoint)
            return response.get('Positions', [])
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise TradeStationAPIError(f"Failed to get positions: {e}")
    
    async def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """Get account information"""
        endpoint = f"/v3/brokerage/accounts/{account_id}"
        
        try:
            response = await self._make_request("GET", endpoint)
            return response
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise TradeStationAPIError(f"Failed to get account info: {e}")
    
    async def build_iron_condor_strategy(
        self,
        symbol: str = 'SPY',
        expiration_date: date = None,
        delta_target: float = 0.3,
        wing_width: int = 10
    ) -> Dict[str, Any]:
        """Build iron condor strategy based on VIX/SPY logic from original scripts"""
        
        if expiration_date is None:
            expiration_date = date.today()
        
        # Format expiration date as MM-DD-YYYY for TradeStation API
        exp_str = f"{expiration_date.month:02d}-{expiration_date.day:02d}-{expiration_date.year}"
        
        try:
            # Get options chain
            chain_data = await self.get_options_chain(symbol, exp_str, proximity=20)
            
            if not chain_data:
                raise TradeStationAPIError("No options chain data received")
            
            # Convert to DataFrame for easier processing
            chain = pd.DataFrame(chain_data)
            chain = chain.set_index(['Strike', 'Side'])
            
            # Calculate delta differences from target (0.3 for puts, -0.3 for calls)
            chain['DDiff'] = chain.apply(
                lambda row: abs(float(row['Delta']) - delta_target) if row.name[1] == 'Put' 
                else abs(float(row['Delta']) + delta_target), axis=1
            )
            
            # Find closest strikes to delta targets
            put_strikes = chain[chain.index.get_level_values(1) == 'Put']
            call_strikes = chain[chain.index.get_level_values(1) == 'Call']
            
            if put_strikes.empty or call_strikes.empty:
                raise TradeStationAPIError("Insufficient options data for iron condor")
            
            # Find optimal strikes
            put_index = put_strikes['DDiff'].idxmin()
            call_index = call_strikes['DDiff'].idxmin()
            
            put_strike = int(put_index[0])
            call_strike = int(call_index[0])
            put_wing_strike = put_strike - wing_width
            call_wing_strike = call_strike + wing_width
            
            # Get pricing data
            put_bid = float(chain.loc[(str(put_strike), 'Put')]['Bid'])
            call_bid = float(chain.loc[(str(call_strike), 'Call')]['Bid'])
            put_wing_ask = float(chain.loc[(str(put_wing_strike), 'Put')]['Ask'])
            call_wing_ask = float(chain.loc[(str(call_wing_strike), 'Call')]['Ask'])
            
            # Calculate strategy metrics
            max_profit = put_bid + call_bid - put_wing_ask - call_wing_ask
            max_profit = math.floor(max_profit * 100) / 100  # Round down to nearest penny
            max_loss = wing_width - max_profit
            
            # Format option symbols (YYMMDD format)
            opt_date = f"{expiration_date.year % 100:02d}{expiration_date.month:02d}{expiration_date.day:02d}"
            
            strategy_info = {
                'symbol': symbol,
                'expiration_date': expiration_date,
                'put_strike': put_strike,
                'call_strike': call_strike,
                'put_wing_strike': put_wing_strike,
                'call_wing_strike': call_wing_strike,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'net_credit': max_profit,
                'option_symbols': {
                    'put_sell': f'{symbol} {opt_date}P{put_strike}',
                    'put_buy': f'{symbol} {opt_date}P{put_wing_strike}',
                    'call_sell': f'{symbol} {opt_date}C{call_strike}',
                    'call_buy': f'{symbol} {opt_date}C{call_wing_strike}'
                },
                'take_profit_price': math.floor(max_profit * 0.25 * 100) / 100  # 25% take profit
            }
            
            logger.info(f"Iron condor strategy built: {strategy_info}")
            return strategy_info
            
        except Exception as e:
            logger.error(f"Error building iron condor strategy: {e}")
            raise TradeStationAPIError(f"Failed to build iron condor: {e}")
    
    async def place_iron_condor_order(
        self,
        account_id: str,
        strategy_info: Dict[str, Any],
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Place iron condor order with take profit"""
        
        try:
            # Build the main iron condor order
            order_payload = {
                "AccountID": account_id,
                "OrderType": "Market",
                "TimeInForce": {
                    "Duration": "DAY"
                },
                "Legs": [
                    {
                        "Symbol": strategy_info['option_symbols']['put_buy'],
                        "Quantity": quantity,
                        "TradeAction": "BUYTOOPEN"
                    },
                    {
                        "Symbol": strategy_info['option_symbols']['put_sell'],
                        "Quantity": quantity,
                        "TradeAction": "SELLTOOPEN"
                    },
                    {
                        "Symbol": strategy_info['option_symbols']['call_sell'],
                        "Quantity": quantity,
                        "TradeAction": "SELLTOOPEN"
                    },
                    {
                        "Symbol": strategy_info['option_symbols']['call_buy'],
                        "Quantity": quantity,
                        "TradeAction": "BUYTOOPEN"
                    }
                ],
                "OSOs": [
                    {
                        "Type": "Normal",
                        "Orders": [
                            {
                                "AccountID": account_id,
                                "OrderType": "Limit",
                                "LimitPrice": str(strategy_info['take_profit_price']),
                                "TimeInForce": {
                                    "Duration": "GTC"
                                },
                                "Legs": [
                                    {
                                        "Symbol": strategy_info['option_symbols']['put_buy'],
                                        "Quantity": quantity,
                                        "TradeAction": "SELLTOCLOSE"
                                    },
                                    {
                                        "Symbol": strategy_info['option_symbols']['put_sell'],
                                        "Quantity": quantity,
                                        "TradeAction": "BUYTOCLOSE"
                                    },
                                    {
                                        "Symbol": strategy_info['option_symbols']['call_sell'],
                                        "Quantity": quantity,
                                        "TradeAction": "BUYTOCLOSE"
                                    },
                                    {
                                        "Symbol": strategy_info['option_symbols']['call_buy'],
                                        "Quantity": quantity,
                                        "TradeAction": "SELLTOCLOSE"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            
            # Place the order
            result = await self.place_order(order_payload)
            
            logger.info(f"Iron condor order placed: {result}")
            return {
                'order_result': result,
                'strategy_info': strategy_info,
                'order_payload': order_payload
            }
            
        except Exception as e:
            logger.error(f"Error placing iron condor order: {e}")
            raise TradeStationAPIError(f"Failed to place iron condor order: {e}")
    
    async def close_iron_condor_position(
        self,
        account_id: str,
        strategy_info: Dict[str, Any],
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Force close iron condor position (for timed exit)"""
        
        try:
            # Build closing order (reverse all positions)
            order_payload = {
                "AccountID": account_id,
                "OrderType": "Market",
                "TimeInForce": {
                    "Duration": "DAY"
                },
                "Legs": [
                    {
                        "Symbol": strategy_info['option_symbols']['put_buy'],
                        "Quantity": quantity,
                        "TradeAction": "SELLTOCLOSE"
                    },
                    {
                        "Symbol": strategy_info['option_symbols']['put_sell'],
                        "Quantity": quantity,
                        "TradeAction": "BUYTOCLOSE"
                    },
                    {
                        "Symbol": strategy_info['option_symbols']['call_sell'],
                        "Quantity": quantity,
                        "TradeAction": "BUYTOCLOSE"
                    },
                    {
                        "Symbol": strategy_info['option_symbols']['call_buy'],
                        "Quantity": quantity,
                        "TradeAction": "SELLTOCLOSE"
                    }
                ]
            }
            
            # Place the closing order
            result = await self.place_order(order_payload)
            
            logger.info(f"Iron condor closing order placed: {result}")
            return {
                'order_result': result,
                'strategy_info': strategy_info,
                'order_payload': order_payload
            }
            
        except Exception as e:
            logger.error(f"Error closing iron condor position: {e}")
            raise TradeStationAPIError(f"Failed to close iron condor position: {e}")