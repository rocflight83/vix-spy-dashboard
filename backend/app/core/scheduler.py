from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
import pytz
import logging
from datetime import datetime, date
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from app.core.config import settings

logger = logging.getLogger(__name__)

class TradingScheduler:
    def __init__(self):
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        self.scheduler = AsyncIOScheduler(
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.timezone('US/Eastern')
        )
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Set up scheduled trading jobs"""
        # Entry job: Run at market open + 2 minutes (9:32 AM ET)
        self.scheduler.add_job(
            self._execute_entry_logic,
            CronTrigger(
                hour=settings.ENTRY_SCHEDULE_HOUR,
                minute=settings.ENTRY_SCHEDULE_MINUTE,
                second=0,
                timezone=pytz.timezone('US/Eastern')
            ),
            id='entry_job',
            name='VIX Iron Condor Entry',
            replace_existing=True
        )
        
        # Exit job: Run at 11:30 AM ET
        self.scheduler.add_job(
            self._execute_exit_logic,
            CronTrigger(
                hour=settings.EXIT_SCHEDULE_HOUR,
                minute=settings.EXIT_SCHEDULE_MINUTE,
                second=0,
                timezone=pytz.timezone('US/Eastern')
            ),
            id='exit_job',
            name='VIX Iron Condor Exit',
            replace_existing=True
        )
        
        logger.info("Trading jobs scheduled:")
        logger.info(f"Entry: {settings.ENTRY_SCHEDULE_HOUR}:{settings.ENTRY_SCHEDULE_MINUTE:02d} ET")
        logger.info(f"Exit: {settings.EXIT_SCHEDULE_HOUR}:{settings.EXIT_SCHEDULE_MINUTE:02d} ET")
    
    def is_trading_day(self, check_date: date = None) -> bool:
        """Check if given date is a trading day (weekday, not holiday)"""
        if check_date is None:
            check_date = date.today()
        
        # Check if weekday (Monday=0, Sunday=6)
        if check_date.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check for US federal holidays
        cal = USFederalHolidayCalendar()
        holidays = cal.holidays(start=check_date, end=check_date, return_name=True)
        
        return len(holidays) == 0
    
    async def _execute_entry_logic(self):
        """Execute entry logic if conditions are met"""
        if not self.is_trading_day():
            logger.info("Skipping entry - not a trading day")
            return
        
        logger.info("=== EXECUTING SCHEDULED ENTRY LOGIC ===")
        logger.info(f"Time: {datetime.now(pytz.timezone('US/Eastern'))}")
        
        try:
            from app.services.trading_engine import TradingEngine
            engine = TradingEngine()
            result = await engine.execute_entry()
            
            if result["success"]:
                logger.info(f"Entry logic completed successfully: {result['message']}")
            else:
                logger.warning(f"Entry logic skipped: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error in scheduled entry: {e}", exc_info=True)
    
    async def _execute_exit_logic(self):
        """Execute exit logic if positions exist"""
        if not self.is_trading_day():
            logger.info("Skipping exit - not a trading day")
            return
        
        logger.info("=== EXECUTING SCHEDULED EXIT LOGIC ===")
        logger.info(f"Time: {datetime.now(pytz.timezone('US/Eastern'))}")
        
        try:
            from app.services.trading_engine import TradingEngine
            engine = TradingEngine()
            result = await engine.execute_exit()
            
            if result["success"]:
                logger.info(f"Exit logic completed: {result['message']}")
            else:
                logger.warning(f"Exit logic failed: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error in scheduled exit: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Trading scheduler started")
    
    def shutdown(self, wait=True):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Trading scheduler stopped")
    
    def get_next_run_times(self):
        """Get next scheduled run times"""
        jobs = {}
        for job in self.scheduler.get_jobs():
            jobs[job.id] = {
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }
        return jobs
    
    def pause_jobs(self):
        """Pause all scheduled jobs"""
        for job in self.scheduler.get_jobs():
            job.pause()
        logger.info("All trading jobs paused")
    
    def resume_jobs(self):
        """Resume all scheduled jobs"""
        for job in self.scheduler.get_jobs():
            job.resume()
        logger.info("All trading jobs resumed")

# Global scheduler instance
scheduler = TradingScheduler()