import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
from app.services.pdt_compliance import PDTComplianceService

class TestPDTComplianceService:
    
    @pytest.fixture
    def pdt_service(self):
        """Create PDT compliance service"""
        return PDTComplianceService()
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_check_pdt_compliance_no_trades(self, mock_session, pdt_service):
        """Test PDT compliance check with no trades"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = pdt_service.check_pdt_compliance("sim")
        
        assert result["total_day_trades"] == 0
        assert result["max_allowed_trades"] == 3
        assert result["trades_remaining"] == 3
        assert result["is_compliant"] == True
        assert result["violation_risk"] == False
        assert result["recent_records"] == []
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_check_pdt_compliance_with_trades(self, mock_session, pdt_service):
        """Test PDT compliance with existing trades"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock PDT records
        mock_records = []
        for i in range(2):
            record = Mock()
            record.trade_count = 1
            record.is_pdt_violation = False
            record.trade_date = date.today() - timedelta(days=i)
            mock_records.append(record)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records
        
        result = pdt_service.check_pdt_compliance("sim")
        
        assert result["total_day_trades"] == 2
        assert result["trades_remaining"] == 1
        assert result["is_compliant"] == True
        assert result["violation_risk"] == True  # Close to limit
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_check_pdt_compliance_violation(self, mock_session, pdt_service):
        """Test PDT compliance with violation"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock PDT records with violation
        mock_records = []
        for i in range(4):
            record = Mock()
            record.trade_count = 1 if i < 3 else 2  # 5 total trades
            record.is_pdt_violation = i == 3  # Violation on 4th day
            record.trade_date = date.today() - timedelta(days=i)
            mock_records.append(record)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records
        
        result = pdt_service.check_pdt_compliance("sim")
        
        assert result["total_day_trades"] == 5
        assert result["trades_remaining"] == 0
        assert result["is_compliant"] == False  # Violation exists
        assert result["violation_risk"] == True
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_can_trade_today_success(self, mock_session, pdt_service):
        """Test can trade today when compliant"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # No trades today
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock compliance check
        with patch.object(pdt_service, 'check_pdt_compliance') as mock_compliance:
            mock_compliance.return_value = {
                "trades_remaining": 2,
                "is_compliant": True
            }
            
            result = pdt_service._can_trade_today(mock_db, "sim")
            assert result == True
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_can_trade_today_already_traded(self, mock_session, pdt_service):
        """Test can trade today when already traded"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Already traded today
        today_record = Mock()
        today_record.trade_count = 1
        mock_db.query.return_value.filter.return_value.first.return_value = today_record
        
        result = pdt_service._can_trade_today(mock_db, "sim")
        assert result == False
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_record_day_trade_new_record(self, mock_session, pdt_service):
        """Test recording day trade with new record"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # No existing record for today
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock compliance check
        with patch.object(pdt_service, 'check_pdt_compliance') as mock_compliance:
            mock_compliance.return_value = {"total_day_trades": 1}
            
            result = pdt_service.record_day_trade("sim")
            
            assert result["success"] == True
            assert result["trade_count"] == 1
            assert result["is_violation"] == False
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_record_day_trade_existing_record(self, mock_session, pdt_service):
        """Test recording day trade with existing record"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Existing record for today
        existing_record = Mock()
        existing_record.trade_count = 1
        mock_db.query.return_value.filter.return_value.first.return_value = existing_record
        
        # Mock compliance check
        with patch.object(pdt_service, 'check_pdt_compliance') as mock_compliance:
            mock_compliance.return_value = {"total_day_trades": 2}
            
            result = pdt_service.record_day_trade("sim")
            
            assert result["success"] == True
            assert existing_record.trade_count == 2  # Incremented
            mock_db.add.assert_not_called()  # No new record added
            mock_db.commit.assert_called_once()
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_record_day_trade_violation(self, mock_session, pdt_service):
        """Test recording day trade that causes violation"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Existing record for today
        existing_record = Mock()
        existing_record.trade_count = 2
        existing_record.is_pdt_violation = False
        mock_db.query.return_value.filter.return_value.first.return_value = existing_record
        
        # Mock compliance check showing violation
        with patch.object(pdt_service, 'check_pdt_compliance') as mock_compliance:
            mock_compliance.return_value = {"total_day_trades": 4}  # Over limit
            
            result = pdt_service.record_day_trade("sim")
            
            assert result["success"] == True
            assert existing_record.trade_count == 3
            assert existing_record.is_pdt_violation == True  # Violation flagged
    
    @patch('app.services.pdt_compliance.SessionLocal')
    def test_reset_pdt_tracking(self, mock_session, pdt_service):
        """Test resetting PDT tracking"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock delete operation
        mock_db.query.return_value.filter.return_value.delete.return_value = 5
        
        result = pdt_service.reset_pdt_tracking("sim")
        
        assert result["success"] == True
        assert result["deleted_records"] == 5
        mock_db.commit.assert_called_once()
    
    def test_get_trading_days_in_period(self, pdt_service):
        """Test getting trading days in period"""
        # Test a known period (1 week)
        start_date = date(2023, 12, 4)  # Monday
        end_date = date(2023, 12, 8)    # Friday
        
        # Should be 5 trading days (Mon-Fri)
        trading_days = pdt_service.get_trading_days_in_period(start_date, end_date)
        
        assert trading_days == 5
    
    def test_max_day_trades_constant(self, pdt_service):
        """Test that max day trades is set correctly"""
        assert pdt_service.max_day_trades == 3
        assert pdt_service.rolling_days == 5