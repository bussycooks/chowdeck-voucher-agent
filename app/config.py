"""Configuration management for the application."""
import os
from typing import Optional
from pydantic import BaseSettings
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # X API Configuration
    x_bearer_token: str
    x_username: str = "lordbinary_"
    
    # Telegram Configuration
    telegram_bot_token: str
    telegram_chat_id: str
    
    # Scheduler Configuration
    monitor_timezone: str = "Africa/Lagos"
    monitor_start: str = "18:00"
    monitor_end: str = "23:00"
    monitor_interval_seconds: int = 60
    
    # Application Configuration
    app_mode: str = "production"
    log_level: str = "INFO"
    database_path: str = "chowdeck_monitor.db"
    
    # Playwright/Chowdeck Configuration
    chowdeck_browser_headless: bool = False
    chowdeck_profile_path: str = "./browser_profiles/chowdeck"
    chowdeck_timeout_ms: int = 30000
    
    # Voucher Extraction Configuration
    voucher_min_length: int = 3
    voucher_max_length: int = 20
    voucher_pattern: str = r"^[A-Z0-9]+$"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def validate_required_secrets(self) -> bool:
        """Validate that all required secrets are configured."""
        required = ["x_bearer_token", "telegram_bot_token", "telegram_chat_id"]
        missing = [field for field in required if not getattr(self, field, None)]
        
        if missing:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
            return False
        return True


def get_settings() -> Settings:
    """Load settings from environment."""
    return Settings()
