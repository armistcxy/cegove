from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Consul Configuration
    CONSUL_ADDR: str
    CONSUL_USER: Optional[str] = None
    CONSUL_PASSWORD: Optional[str] = None
    
    # Database (will be loaded from Consul)
    DATABASE_URL: str = ""
    
    # Service
    SERVICE_NAME: str = "comment-service"
    SERVICE_PORT: int = 8003
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key"  # Default fallback
    
    # Comment-specific settings
    MAX_COMMENT_LENGTH: int = 2000
    AUTO_FLAG_THRESHOLD: int = 3  # Number of reports before auto-flagging
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Load settings from .env and Consul"""
    # Load basic settings from .env
    settings = Settings()
    
    # Load additional config from Consul
    try:
        from .consul_loader import ConsulConfigLoader
        
        loader = ConsulConfigLoader(
            consul_addr=settings.CONSUL_ADDR,
            user=settings.CONSUL_USER,
            password=settings.CONSUL_PASSWORD
        )
        
        # Load config from Consul KV
        consul_config = loader.load_config("service/comment-service.json")
        
        # Update settings with Consul values
        for key, value in consul_config.items():
            key_upper = key.upper()
            if hasattr(settings, key_upper):
                setattr(settings, key_upper, value)
                print(f"Loaded from Consul: {key_upper}")
    
    except Exception as e:
        print(f"Warning: Failed to load config from Consul: {e}")
        # Fall back to .env values if Consul fails
    
    return settings


settings = get_settings()
