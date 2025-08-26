"""
Application settings using Pydantic for environment variable management.
"""
from typing import List, Optional
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application
    APP_NAME: str = "GoodEats Recipe PWA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Database
    DATABASE_URL: str
    
    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Development settings
    RELOAD: bool = False
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.DEBUG or self.RELOAD
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list of strings."""
        return [str(origin) for origin in self.CORS_ORIGINS]


# Global settings instance
settings = Settings()