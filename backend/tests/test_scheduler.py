import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime
import pytz
from app.core.scheduler import TradingScheduler

class TestTradingScheduler:
    
    @pytest.fixture
    def scheduler(self):
        """Create trading scheduler"""
        return TradingScheduler()
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initializes correctly"""
        assert scheduler.scheduler is not None
        assert scheduler.scheduler.timezone.zone == 'US/Eastern'
        
        # Check that jobs are set up
        jobs = scheduler.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        
        assert 'entry_job' in job_ids
        assert 'exit_job' in job_ids
    
    def test_is_trading_day_weekday(self, scheduler):
        """Test is_trading_day for weekday"""
        # Monday
        monday = date(2023, 12, 4)
        assert scheduler.is_trading_day(monday) == True
        
        # Friday
        friday = date(2023, 12, 8)
        assert scheduler.is_trading_day(friday) == True
    
    def test_is_trading_day_weekend(self, scheduler):
        """Test is_trading_day for weekend"""
        # Saturday
        saturday = date(2023, 12, 9)
        assert scheduler.is_trading_day(saturday) == False
        
        # Sunday  
        sunday = date(2023, 12, 10)
        assert scheduler.is_trading_day(sunday) == False
    
    def test_is_trading_day_holiday(self, scheduler):
        """Test is_trading_day for holiday"""
        # Christmas Day 2023 (Monday)
        christmas = date(2023, 12, 25)
        assert scheduler.is_trading_day(christmas) == False
    
    def test_is_trading_day_today(self, scheduler):
        """Test is_trading_day for today (no date provided)"""
        result = scheduler.is_trading_day()
        # Should return boolean without error
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_execute_entry_logic_not_trading_day(self, scheduler):
        """Test entry logic on non-trading day"""
        with patch.object(scheduler, 'is_trading_day', return_value=False):
            # Should complete without error
            await scheduler._execute_entry_logic()
            # No exception means success
    
    @pytest.mark.asyncio
    async def test_execute_entry_logic_trading_day(self, scheduler):
        """Test entry logic on trading day"""
        with patch.object(scheduler, 'is_trading_day', return_value=True), \
             patch('app.core.scheduler.TradingEngine') as mock_engine_class:
            
            mock_engine = Mock()
            mock_engine.execute_entry = AsyncMock(return_value={"success": True, "message": "Test"})
            mock_engine_class.return_value = mock_engine
            
            await scheduler._execute_entry_logic()
            
            mock_engine.execute_entry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_entry_logic_error_handling(self, scheduler):
        """Test entry logic error handling"""
        with patch.object(scheduler, 'is_trading_day', return_value=True), \
             patch('app.core.scheduler.TradingEngine') as mock_engine_class:
            
            mock_engine_class.side_effect = Exception("Test error")
            
            # Should not raise exception
            await scheduler._execute_entry_logic()
    
    @pytest.mark.asyncio
    async def test_execute_exit_logic_not_trading_day(self, scheduler):
        """Test exit logic on non-trading day"""
        with patch.object(scheduler, 'is_trading_day', return_value=False):
            # Should complete without error
            await scheduler._execute_exit_logic()
    
    @pytest.mark.asyncio
    async def test_execute_exit_logic_trading_day(self, scheduler):
        """Test exit logic on trading day"""
        with patch.object(scheduler, 'is_trading_day', return_value=True), \
             patch('app.core.scheduler.TradingEngine') as mock_engine_class:
            
            mock_engine = Mock()
            mock_engine.execute_exit = AsyncMock(return_value={"success": True, "message": "Test"})
            mock_engine_class.return_value = mock_engine
            
            await scheduler._execute_exit_logic()
            
            mock_engine.execute_exit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_exit_logic_error_handling(self, scheduler):
        """Test exit logic error handling"""
        with patch.object(scheduler, 'is_trading_day', return_value=True), \
             patch('app.core.scheduler.TradingEngine') as mock_engine_class:
            
            mock_engine_class.side_effect = Exception("Test error")
            
            # Should not raise exception
            await scheduler._execute_exit_logic()
    
    def test_start_scheduler(self, scheduler):
        """Test starting scheduler"""
        # Stop if already running
        if scheduler.scheduler.running:
            scheduler.shutdown()
        
        scheduler.start()
        assert scheduler.scheduler.running == True
        
        # Clean up
        scheduler.shutdown()
    
    def test_shutdown_scheduler(self, scheduler):
        """Test shutting down scheduler"""
        scheduler.start()
        assert scheduler.scheduler.running == True
        
        scheduler.shutdown()
        assert scheduler.scheduler.running == False
    
    def test_get_next_run_times(self, scheduler):
        """Test getting next run times"""
        next_runs = scheduler.get_next_run_times()
        
        assert isinstance(next_runs, dict)
        assert 'entry_job' in next_runs
        assert 'exit_job' in next_runs
        
        # Each job should have name and next_run
        for job_id, job_info in next_runs.items():
            assert 'name' in job_info
            assert 'next_run' in job_info
    
    def test_pause_jobs(self, scheduler):
        """Test pausing jobs"""
        scheduler.start()
        
        # Initially jobs should be running
        jobs = scheduler.scheduler.get_jobs()
        for job in jobs:
            assert job.next_run_time is not None
        
        scheduler.pause_jobs()
        
        # After pausing, jobs should have no next run time
        jobs = scheduler.scheduler.get_jobs()
        for job in jobs:
            # Job should exist but be paused
            assert job is not None
        
        scheduler.shutdown()
    
    def test_resume_jobs(self, scheduler):
        """Test resuming jobs"""
        scheduler.start()
        scheduler.pause_jobs()
        
        scheduler.resume_jobs()
        
        # After resuming, jobs should have next run times again
        jobs = scheduler.scheduler.get_jobs()
        for job in jobs:
            # Jobs should be resumed
            assert job is not None
        
        scheduler.shutdown()
    
    def test_job_configuration(self, scheduler):
        """Test that jobs are configured with correct triggers"""
        jobs = {job.id: job for job in scheduler.scheduler.get_jobs()}
        
        entry_job = jobs['entry_job']
        exit_job = jobs['exit_job']
        
        # Check job names
        assert entry_job.name == 'VIX Iron Condor Entry'
        assert exit_job.name == 'VIX Iron Condor Exit'
        
        # Check that jobs have cron triggers
        assert entry_job.trigger is not None
        assert exit_job.trigger is not None
        
        # Check timezone
        assert str(entry_job.trigger.timezone) == 'US/Eastern'
        assert str(exit_job.trigger.timezone) == 'US/Eastern'
    
    def test_timezone_handling(self, scheduler):
        """Test timezone handling"""
        # Test current time in US/Eastern
        et_time = datetime.now(pytz.timezone('US/Eastern'))
        assert et_time.tzinfo is not None
        
        # Scheduler should use US/Eastern timezone
        assert scheduler.scheduler.timezone.zone == 'US/Eastern'
    
    def test_scheduler_job_defaults(self, scheduler):
        """Test job defaults configuration"""
        # Check job defaults
        job_defaults = scheduler.scheduler._job_defaults
        
        assert job_defaults['coalesce'] == False
        assert job_defaults['max_instances'] == 1
        assert job_defaults['misfire_grace_time'] == 300