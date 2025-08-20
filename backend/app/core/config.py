from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    
    # CORS Configuration
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
        env="ALLOWED_HOSTS"
    )
    
    # TradeStation API Configuration
    TRADESTATION_CLIENT_ID: str = Field(env="TRADESTATION_CLIENT_ID")
    TRADESTATION_CLIENT_SECRET: str = Field(env="TRADESTATION_CLIENT_SECRET")
    TRADESTATION_REFRESH_TOKEN: str = Field(env="TRADESTATION_REFRESH_TOKEN")
    
    # Account Configuration
    TRADESTATION_SIM_ACCOUNT: str = Field(default="SIM2818191M", env="TRADESTATION_SIM_ACCOUNT")
    TRADESTATION_LIVE_ACCOUNT: Optional[str] = Field(default=None, env="TRADESTATION_LIVE_ACCOUNT")
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(env="SUPABASE_SERVICE_ROLE_KEY")
    
    # Database Configuration
    DATABASE_URL: str = Field(env="DATABASE_URL")
    
    # Trading Configuration
    STRATEGY_ENABLED: bool = Field(default=False, env="STRATEGY_ENABLED")
    USE_LIVE_ACCOUNT: bool = Field(default=False, env="USE_LIVE_ACCOUNT")
    VIX_SYMBOL: str = Field(default="^VIX", env="VIX_SYMBOL")
    UNDERLYING_SYMBOL: str = Field(default="SPY", env="UNDERLYING_SYMBOL")
    DELTA_TARGET: float = Field(default=0.3, env="DELTA_TARGET")
    WING_WIDTH: int = Field(default=10, env="WING_WIDTH")
    TAKE_PROFIT_PERCENTAGE: float = Field(default=0.25, env="TAKE_PROFIT_PERCENTAGE")
    
    # Schedule Configuration (US/Eastern times)
    ENTRY_SCHEDULE_HOUR: int = Field(default=9, env="ENTRY_SCHEDULE_HOUR")
    ENTRY_SCHEDULE_MINUTE: int = Field(default=32, env="ENTRY_SCHEDULE_MINUTE")
    EXIT_SCHEDULE_HOUR: int = Field(default=11, env="EXIT_SCHEDULE_HOUR")
    EXIT_SCHEDULE_MINUTE: int = Field(default=30, env="EXIT_SCHEDULE_MINUTE")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="app.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def get_tradestation_base_url(self) -> str:
        """Get TradeStation API base URL based on account type"""
        if self.USE_LIVE_ACCOUNT:
            return "https://api.tradestation.com"
        return "https://sim-api.tradestation.com"
    
    def get_account_id(self) -> str:
        """Get current account ID based on account type"""
        if self.USE_LIVE_ACCOUNT and self.TRADESTATION_LIVE_ACCOUNT:
            return self.TRADESTATION_LIVE_ACCOUNT
        return self.TRADESTATION_SIM_ACCOUNT

settings = Settings()