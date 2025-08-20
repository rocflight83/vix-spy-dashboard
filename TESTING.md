# Testing Guide

This document describes how to run tests for the VIX/SPY Iron Condor Trading Dashboard.

## Test Structure

The test suite is located in `backend/tests/` and includes:

- `test_tradestation_api.py` - Tests for TradeStation API integration
- `test_market_data.py` - Tests for market data services (VIX/SPY)
- `test_database.py` - Tests for database models and operations
- `test_api_endpoints.py` - Tests for API endpoints
- `conftest.py` - Test configuration and fixtures

## Prerequisites

1. Install test dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Ensure you have a test environment configuration

## Running Tests

### Run All Tests
```bash
cd backend
pytest
```

### Run Tests with Coverage
```bash
cd backend
pytest --cov=app --cov-report=html
```

### Run Specific Test Files
```bash
# Test only TradeStation API
pytest tests/test_tradestation_api.py

# Test only database models
pytest tests/test_database.py

# Test only API endpoints
pytest tests/test_api_endpoints.py
```

### Run Specific Test Classes or Methods
```bash
# Run specific test class
pytest tests/test_tradestation_api.py::TestTradeStationAPI

# Run specific test method
pytest tests/test_tradestation_api.py::TestTradeStationAPI::test_get_access_token_success
```

### Run Tests with Verbose Output
```bash
pytest -v
```

### Run Tests in Parallel (if pytest-xdist is installed)
```bash
pip install pytest-xdist
pytest -n auto
```

## Test Categories

### Unit Tests
Test individual components in isolation:
- TradeStation API methods
- Market data processing
- Database model operations
- Configuration handling

### Integration Tests
Test interaction between components:
- API endpoint responses
- Database operations with real queries
- Service layer integration

### Async Tests
Tests for asynchronous operations:
- API requests to TradeStation
- Async database operations
- Background task scheduling

## Test Fixtures

The test suite uses several fixtures defined in `conftest.py`:

- `test_settings` - Mock configuration for testing
- `test_db` - In-memory SQLite database for testing
- `client` - FastAPI test client
- `mock_httpx_client` - Mock HTTP client for API tests
- `mock_yahoo_ticker` - Mock Yahoo Finance data

## Test Data

Tests use:
- Mock data for external API responses
- In-memory SQLite database (automatically cleaned up)
- Realistic market data scenarios
- Edge cases and error conditions

## Continuous Integration

Tests are designed to run in CI/CD environments:
- No external dependencies required
- Uses mocked external services
- Fast execution (< 30 seconds)
- Clear pass/fail status

## Test Coverage Goals

Target coverage areas:
- ✅ **API Authentication** - Token refresh, error handling
- ✅ **Market Data** - VIX gap detection, data storage
- ✅ **Database Models** - CRUD operations, relationships
- ✅ **API Endpoints** - Request/response validation
- ✅ **Configuration** - Settings validation
- ⏳ **Trading Logic** - Entry/exit algorithms (Phase 2)
- ⏳ **Scheduler** - Time-based execution (Phase 2)
- ⏳ **PDT Compliance** - Rule validation (Phase 2)

## Common Test Patterns

### Mocking External Services
```python
@patch('httpx.AsyncClient')
async def test_api_call(mock_client):
    # Mock the external API response
    mock_response = Mock()
    mock_response.json.return_value = {"status": "success"}
    mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
    
    # Test your code
    result = await your_api_function()
    assert result["status"] == "success"
```

### Database Testing
```python
def test_database_operation(test_db):
    db_gen = test_db()
    db = next(db_gen)
    
    # Create test data
    record = YourModel(field="value")
    db.add(record)
    db.commit()
    
    # Test the operation
    result = db.query(YourModel).first()
    assert result.field == "value"
```

### API Endpoint Testing
```python
def test_api_endpoint(client):
    response = client.get("/api/your-endpoint")
    
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

## Debugging Tests

### Run Tests with Debug Output
```bash
pytest -s  # Don't capture output
pytest --pdb  # Drop into debugger on failure
pytest --lf  # Run only last failed tests
```

### View Test Coverage Report
After running tests with coverage:
```bash
# View in browser
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## Performance Tests

For performance-critical components:
```python
import time
import pytest

def test_performance():
    start = time.time()
    
    # Your operation
    result = expensive_operation()
    
    end = time.time()
    assert (end - start) < 1.0  # Should complete in < 1 second
```

## Error Testing

Always test error conditions:
```python
def test_api_error_handling():
    with pytest.raises(YourCustomException):
        function_that_should_raise_error()
```

## Next Steps

As we implement Phase 2 and beyond:
1. Add tests for trading logic
2. Add tests for scheduler functionality
3. Add integration tests with real APIs (in test mode)
4. Add performance benchmarks
5. Add end-to-end tests for complete workflows

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the `backend/` directory
2. **Database Errors**: Test database is automatically created/destroyed
3. **Async Test Issues**: Use `@pytest.mark.asyncio` decorator
4. **Mock Issues**: Ensure mocks are properly configured for the specific test

### Test Environment

Tests run in isolation with:
- Separate test database (SQLite in-memory)
- Mocked external services
- Test-specific configuration
- No side effects on real systems