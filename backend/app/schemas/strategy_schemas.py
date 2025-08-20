from pydantic import BaseModel
from typing import Optional

class StrategyConfigResponse(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class StrategyStatusResponse(BaseModel):
    strategy_enabled: bool
    use_live_account: bool
    account_id: str
    next_entry_time: Optional[str] = None
    next_exit_time: Optional[str] = None
    is_trading_day: bool
    scheduler_running: bool