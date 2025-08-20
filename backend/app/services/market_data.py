from yahooquery import Ticker
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import logging
from app.models.database import SessionLocal, MarketData
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self):
        self.vix_ticker = Ticker('^VIX')
        self.spy_ticker = Ticker('SPY')
    
    def get_vix_data(self, days: int = 5) -> Dict[str, Any]:
        """Get recent VIX data"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            vix_hist = self.vix_ticker.history(period=f'{days}d', interval='1d', end=end_date)
            
            if vix_hist.empty:
                raise Exception("No VIX data received")
            
            # Get the last two days for gap calculation
            recent_data = vix_hist.tail(2)
            
            if len(recent_data) >= 2:
                current_day = recent_data.iloc[-1]
                previous_day = recent_data.iloc[-2]
                
                gap_amount = current_day.open - previous_day.close
                gap_percentage = (gap_amount / previous_day.close) * 100 if previous_day.close != 0 else 0
                
                return {
                    'current_open': float(current_day.open),
                    'current_high': float(current_day.high),
                    'current_low': float(current_day.low),
                    'current_close': float(current_day.close),
                    'previous_close': float(previous_day.close),
                    'gap_amount': float(gap_amount),
                    'gap_percentage': float(gap_percentage),
                    'is_gap_up': gap_amount > 0,
                    'date': current_day.name[1].date() if hasattr(current_day.name, '__getitem__') else date.today()
                }
            else:
                # Only one day of data
                current_day = recent_data.iloc[-1]
                return {
                    'current_open': float(current_day.open),
                    'current_high': float(current_day.high),
                    'current_low': float(current_day.low),
                    'current_close': float(current_day.close),
                    'previous_close': None,
                    'gap_amount': None,
                    'gap_percentage': None,
                    'is_gap_up': False,
                    'date': current_day.name[1].date() if hasattr(current_day.name, '__getitem__') else date.today()
                }
                
        except Exception as e:
            logger.error(f"Error fetching VIX data: {e}")
            raise
    
    def get_spy_price(self) -> float:
        """Get current SPY price"""
        try:
            spy_data = self.spy_ticker.price
            if '^GSPC' in spy_data:
                return float(spy_data['^GSPC']['regularMarketPrice'])
            elif 'SPY' in spy_data:
                return float(spy_data['SPY']['regularMarketPrice'])
            else:
                # Fallback: get from history
                spy_hist = self.spy_ticker.history(period='1d', interval='1d')
                if not spy_hist.empty:
                    return float(spy_hist.iloc[-1].close)
            
            raise Exception("Could not fetch SPY price")
            
        except Exception as e:
            logger.error(f"Error fetching SPY price: {e}")
            raise
    
    def store_market_data(self, symbol: str, data: Dict[str, Any]) -> None:
        """Store market data in database"""
        db = SessionLocal()
        try:
            # Check if data already exists for this date
            existing = db.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.data_date == data['date']
            ).first()
            
            if existing:
                # Update existing record
                existing.open_price = data['current_open']
                existing.high_price = data['current_high']
                existing.low_price = data['current_low']
                existing.close_price = data['current_close']
                existing.previous_close = data.get('previous_close')
                existing.gap_amount = data.get('gap_amount')
                existing.gap_percentage = data.get('gap_percentage')
            else:
                # Create new record
                market_data = MarketData(
                    data_date=data['date'],
                    symbol=symbol,
                    open_price=data['current_open'],
                    high_price=data['current_high'],
                    low_price=data['current_low'],
                    close_price=data['current_close'],
                    previous_close=data.get('previous_close'),
                    gap_amount=data.get('gap_amount'),
                    gap_percentage=data.get('gap_percentage')
                )
                db.add(market_data)
            
            db.commit()
            logger.info(f"Stored {symbol} market data for {data['date']}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing market data: {e}")
            raise
        finally:
            db.close()
    
    def check_vix_gap_up_condition(self) -> Dict[str, Any]:
        """Check if VIX gap up condition is met for entry"""
        try:
            vix_data = self.get_vix_data()
            
            # Store the data for future reference
            self.store_market_data('^VIX', vix_data)
            
            result = {
                'vix_gap_up': vix_data['is_gap_up'],
                'gap_amount': vix_data.get('gap_amount', 0),
                'gap_percentage': vix_data.get('gap_percentage', 0),
                'current_vix': vix_data['current_open'],
                'previous_vix_close': vix_data.get('previous_close'),
                'condition_met': vix_data['is_gap_up'],
                'timestamp': datetime.now()
            }
            
            logger.info(f"VIX gap condition check: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking VIX gap condition: {e}")
            return {
                'vix_gap_up': False,
                'gap_amount': 0,
                'gap_percentage': 0,
                'current_vix': 0,
                'previous_vix_close': 0,
                'condition_met': False,
                'error': str(e),
                'timestamp': datetime.now()
            }