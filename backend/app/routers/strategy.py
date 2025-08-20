from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, StrategyConfig
from app.core.scheduler import scheduler
from app.core.config import settings
from app.schemas.strategy_schemas import StrategyConfigResponse, StrategyStatusResponse
from typing import Dict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status", response_model=StrategyStatusResponse)
async def get_strategy_status(db: Session = Depends(get_db)):
    """Get current strategy status and configuration"""
    
    # Get configuration from database or use defaults
    strategy_enabled = await get_config_value(db, "strategy_enabled", "false") == "true"
    use_live_account = await get_config_value(db, "use_live_account", "false") == "true"
    
    return {
        "strategy_enabled": strategy_enabled,
        "use_live_account": use_live_account,
        "account_id": settings.get_account_id(),
        "next_entry_time": scheduler.get_next_run_times().get("entry_job", {}).get("next_run"),
        "next_exit_time": scheduler.get_next_run_times().get("exit_job", {}).get("next_run"),
        "is_trading_day": scheduler.is_trading_day(),
        "scheduler_running": scheduler.scheduler.running
    }

@router.post("/toggle")
async def toggle_strategy(enabled: bool, db: Session = Depends(get_db)):
    """Toggle strategy on/off"""
    try:
        await set_config_value(db, "strategy_enabled", str(enabled).lower())
        
        if enabled:
            scheduler.resume_jobs()
            message = "Strategy enabled and scheduled jobs resumed"
        else:
            scheduler.pause_jobs()
            message = "Strategy disabled and scheduled jobs paused"
        
        logger.info(f"Strategy toggled: {enabled}")
        return {
            "success": True,
            "strategy_enabled": enabled,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error toggling strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/account/toggle")
async def toggle_account_type(use_live: bool, db: Session = Depends(get_db)):
    """Toggle between sim and live account with safety checks"""
    try:
        # Safety check: Don't allow live account switch without explicit confirmation
        if use_live and not settings.TRADESTATION_LIVE_ACCOUNT:
            raise HTTPException(
                status_code=400, 
                detail="Live account ID not configured. Please set TRADESTATION_LIVE_ACCOUNT in environment."
            )
        
        # Check PDT compliance for live account
        if use_live:
            from app.services.pdt_compliance import PDTComplianceService
            pdt_service = PDTComplianceService()
            pdt_status = pdt_service.check_pdt_compliance("live")
            
            if not pdt_status["is_compliant"]:
                logger.warning("Attempting to switch to live account with PDT violation")
                return {
                    "success": False,
                    "message": "Cannot switch to live account: PDT rule violation",
                    "pdt_status": pdt_status
                }
        
        await set_config_value(db, "use_live_account", str(use_live).lower())
        
        # Update settings runtime value
        settings.USE_LIVE_ACCOUNT = use_live
        
        account_type = "live" if use_live else "sim"
        account_id = settings.get_account_id()
        base_url = settings.get_tradestation_base_url()
        
        # Verify API access with new account setting
        from app.services.tradestation_api import TradeStationAPI
        try:
            api = TradeStationAPI()
            token = await api.get_access_token()
            api_status = "connected"
        except Exception as api_error:
            api_status = f"error: {str(api_error)}"
        
        logger.info(f"Account switched to: {account_type} ({account_id})")
        return {
            "success": True,
            "use_live_account": use_live,
            "account_type": account_type,
            "account_id": account_id,
            "api_base_url": base_url,
            "api_status": api_status,
            "message": f"Successfully switched to {account_type} account",
            "warning": "LIVE TRADING ENABLED - Real money at risk!" if use_live else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", response_model=Dict[str, str])
async def get_all_config(db: Session = Depends(get_db)):
    """Get all strategy configuration"""
    configs = db.query(StrategyConfig).all()
    return {config.config_key: config.config_value for config in configs}

@router.post("/config")
async def update_config(config_updates: Dict[str, str], db: Session = Depends(get_db)):
    """Update strategy configuration"""
    try:
        for key, value in config_updates.items():
            await set_config_value(db, key, value)
        
        return {
            "success": True,
            "message": f"Updated {len(config_updates)} configuration items",
            "updated_configs": config_updates
        }
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manual/entry")
async def manual_entry():
    """Manually trigger entry logic"""
    try:
        from app.services.trading_engine import TradingEngine
        engine = TradingEngine()
        result = await engine.execute_entry()
        return {
            "success": True,
            "message": "Manual entry executed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in manual entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manual/exit")
async def manual_exit():
    """Manually trigger exit logic"""
    try:
        from app.services.trading_engine import TradingEngine
        engine = TradingEngine()
        result = await engine.execute_exit()
        return {
            "success": True,
            "message": "Manual exit executed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in manual exit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def get_config_value(db: Session, key: str, default: str = None) -> str:
    """Get configuration value from database"""
    config = db.query(StrategyConfig).filter(StrategyConfig.config_key == key).first()
    return config.config_value if config else default

async def set_config_value(db: Session, key: str, value: str, description: str = None):
    """Set configuration value in database"""
    config = db.query(StrategyConfig).filter(StrategyConfig.config_key == key).first()
    
    if config:
        config.config_value = value
        if description:
            config.description = description
    else:
        config = StrategyConfig(
            config_key=key,
            config_value=value,
            description=description
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)