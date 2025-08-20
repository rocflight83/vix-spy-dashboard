from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.models.database import get_db
from app.core.scheduler import scheduler
from app.services.tradestation_api import TradeStationAPI
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VIX/SPY Trading Dashboard"
    }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including all system components"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    overall_healthy = True
    
    # Check database connection
    try:
        db.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        overall_healthy = False
    
    # Check scheduler status
    try:
        scheduler_running = scheduler.scheduler.running
        next_runs = scheduler.get_next_run_times()
        health_status["components"]["scheduler"] = {
            "status": "healthy" if scheduler_running else "unhealthy",
            "running": scheduler_running,
            "next_runs": next_runs
        }
        if not scheduler_running:
            overall_healthy = False
    except Exception as e:
        health_status["components"]["scheduler"] = {
            "status": "unhealthy",
            "message": f"Scheduler error: {str(e)}"
        }
        overall_healthy = False
    
    # Check TradeStation API connectivity
    try:
        api = TradeStationAPI()
        token = await api.get_access_token()
        health_status["components"]["tradestation_api"] = {
            "status": "healthy",
            "message": "API authentication successful",
            "has_token": bool(token)
        }
    except Exception as e:
        health_status["components"]["tradestation_api"] = {
            "status": "unhealthy",
            "message": f"TradeStation API error: {str(e)}"
        }
        overall_healthy = False
    
    # Check if today is a trading day
    is_trading_day = scheduler.is_trading_day()
    health_status["components"]["market_status"] = {
        "status": "info",
        "is_trading_day": is_trading_day,
        "date": date.today().isoformat()
    }
    
    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    if not overall_healthy:
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/scheduler")
async def scheduler_status():
    """Get detailed scheduler status"""
    try:
        return {
            "running": scheduler.scheduler.running,
            "next_runs": scheduler.get_next_run_times(),
            "is_trading_day": scheduler.is_trading_day(),
            "timezone": str(scheduler.scheduler.timezone)
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))