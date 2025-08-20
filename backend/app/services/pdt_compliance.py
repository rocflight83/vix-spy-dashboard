from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Dict, Any
import logging
from app.models.database import PDTTracking, Trade, SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

class PDTComplianceService:
    """Pattern Day Trading compliance service for accounts under $25k"""
    
    def __init__(self):
        self.max_day_trades = 3  # Maximum day trades in rolling 5-day period
        self.rolling_days = 5
    
    def check_pdt_compliance(self, account_type: str = None) -> Dict[str, Any]:
        """Check current PDT compliance status"""
        if account_type is None:
            account_type = "live" if settings.USE_LIVE_ACCOUNT else "sim"
        
        db = SessionLocal()
        try:
            # Get last 5 trading days
            end_date = date.today()
            start_date = end_date - timedelta(days=7)  # Go back 7 days to catch 5 trading days
            
            # Get PDT records for the period
            pdt_records = db.query(PDTTracking).filter(
                PDTTracking.trade_date >= start_date,
                PDTTracking.trade_date <= end_date,
                PDTTracking.account_type == account_type
            ).order_by(PDTTracking.trade_date.desc()).limit(5).all()
            
            # Calculate total day trades
            total_day_trades = sum(record.trade_count for record in pdt_records)
            trades_remaining = max(0, self.max_day_trades - total_day_trades)
            
            # Check for violations
            has_violation = any(record.is_pdt_violation for record in pdt_records)
            violation_risk = total_day_trades >= (self.max_day_trades - 1)
            
            return {
                "total_day_trades": total_day_trades,
                "max_allowed_trades": self.max_day_trades,
                "trades_remaining": trades_remaining,
                "is_compliant": total_day_trades <= self.max_day_trades and not has_violation,
                "violation_risk": violation_risk,
                "can_trade_today": self._can_trade_today(db, account_type),
                "recent_records": [{
                    "date": record.trade_date.isoformat(),
                    "trade_count": record.trade_count,
                    "is_violation": record.is_pdt_violation
                } for record in pdt_records]
            }
            
        except Exception as e:
            logger.error(f"Error checking PDT compliance: {e}")
            return {
                "total_day_trades": 0,
                "max_allowed_trades": self.max_day_trades,
                "trades_remaining": self.max_day_trades,
                "is_compliant": False,
                "violation_risk": False,
                "can_trade_today": False,
                "error": str(e),
                "recent_records": []
            }
        finally:
            db.close()
    
    def _can_trade_today(self, db: Session, account_type: str) -> bool:
        """Check if we can make a day trade today without violating PDT rules"""
        today = date.today()
        
        # Check if we've already made a trade today
        today_record = db.query(PDTTracking).filter(
            PDTTracking.trade_date == today,
            PDTTracking.account_type == account_type
        ).first()
        
        if today_record and today_record.trade_count > 0:
            logger.info(f"Already made {today_record.trade_count} trades today")
            return False
        
        # Get last 5 trading days (excluding today)
        end_date = today - timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        
        # Get PDT records for the period
        pdt_records = db.query(PDTTracking).filter(
            PDTTracking.trade_date >= start_date,
            PDTTracking.trade_date <= end_date,
            PDTTracking.account_type == account_type
        ).order_by(PDTTracking.trade_date.desc()).limit(5).all()
        
        # Calculate total day trades in rolling period
        total_day_trades = sum(record.trade_count for record in pdt_records)
        trades_remaining = max(0, self.max_day_trades - total_day_trades)
        
        # Check for violations
        has_violation = any(record.is_pdt_violation for record in pdt_records)
        
        can_trade = trades_remaining > 0 and not has_violation
        
        logger.info(f"PDT compliance check: can_trade={can_trade}, trades_remaining={trades_remaining}")
        return can_trade
    
    def record_day_trade(self, account_type: str = None) -> Dict[str, Any]:
        """Record a day trade and update PDT tracking"""
        if account_type is None:
            account_type = "live" if settings.USE_LIVE_ACCOUNT else "sim"
        
        db = SessionLocal()
        try:
            today = date.today()
            
            # Get or create today's PDT record
            pdt_record = db.query(PDTTracking).filter(
                PDTTracking.trade_date == today,
                PDTTracking.account_type == account_type
            ).first()
            
            if pdt_record:
                # Update existing record
                pdt_record.trade_count += 1
            else:
                # Create new record
                pdt_record = PDTTracking(
                    trade_date=today,
                    account_type=account_type,
                    trade_count=1,
                    is_pdt_violation=False
                )
                db.add(pdt_record)
            
            # Check if this trade causes a violation
            compliance = self.check_pdt_compliance(account_type)
            if compliance["total_day_trades"] > self.max_day_trades:
                pdt_record.is_pdt_violation = True
                logger.warning(f"PDT violation recorded for {account_type} account on {today}")
            
            db.commit()
            db.refresh(pdt_record)
            
            logger.info(f"Day trade recorded: {account_type} account, count: {pdt_record.trade_count}")
            
            return {
                "success": True,
                "trade_count": pdt_record.trade_count,
                "is_violation": pdt_record.is_pdt_violation,
                "trades_remaining": max(0, self.max_day_trades - pdt_record.trade_count),
                "message": f"Day trade recorded for {today}"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error recording day trade: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to record day trade"
            }
        finally:
            db.close()
    
    def reset_pdt_tracking(self, account_type: str = None) -> Dict[str, Any]:
        """Reset PDT tracking (for testing purposes)"""
        if account_type is None:
            account_type = "live" if settings.USE_LIVE_ACCOUNT else "sim"
        
        db = SessionLocal()
        try:
            # Delete all PDT records for this account type
            deleted = db.query(PDTTracking).filter(
                PDTTracking.account_type == account_type
            ).delete()
            
            db.commit()
            
            logger.info(f"Reset PDT tracking for {account_type} account: {deleted} records deleted")
            
            return {
                "success": True,
                "deleted_records": deleted,
                "message": f"PDT tracking reset for {account_type} account"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting PDT tracking: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to reset PDT tracking"
            }
        finally:
            db.close()
    
    def get_trading_days_in_period(self, start_date: date, end_date: date) -> int:
        """Get number of trading days in a period (excluding weekends and holidays)"""
        import pandas as pd
        from pandas.tseries.holiday import USFederalHolidayCalendar
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Filter out weekends
        business_days = date_range[date_range.weekday < 5]
        
        # Filter out holidays
        cal = USFederalHolidayCalendar()
        holidays = cal.holidays(start=start_date, end=end_date)
        trading_days = business_days.difference(holidays)
        
        return len(trading_days)