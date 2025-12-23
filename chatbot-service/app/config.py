from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from app.consul_loader import get_consul_loader


class Settings(BaseSettings):
    # Consul Configuration
    CONSUL_ADDR: str = "https://consul.cegove.cloud"
    CONSUL_USER: Optional[str] = None
    CONSUL_PASSWORD: Optional[str] = None
    
    # Gemini
    GEMINI_API_KEY: str = ""
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Microservices
    MOVIE_SERVICE_URL: str = ""
    BOOKING_SERVICE_URL: str = ""
    CINEMA_SERVICE_URL: str = ""
    
    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    
    # Service
    SERVICE_NAME: str = "chatbot-service"
    SERVICE_PORT: int = 8004
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Chatbot-specific settings
    MAX_MESSAGE_LENGTH: int = 2000
    SESSION_TTL: int = 86400  # 24 hours in seconds
    
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
        from app.consul_loader import ConsulConfigLoader
        
        loader = ConsulConfigLoader(
            consul_addr=settings.CONSUL_ADDR,
            user=settings.CONSUL_USER,
            password=settings.CONSUL_PASSWORD
        )
        
        # Load config from Consul KV
        consul_config = loader.load_config("service/chatbot-service.json")
        
        # Update settings with Consul values
        for key, value in consul_config.items():
            key_upper = key.upper()
            if hasattr(settings, key_upper):
                setattr(settings, key_upper, value)
                # Hide sensitive values in logs
                if key_upper in ['GEMINI_API_KEY', 'JWT_SECRET_KEY']:
                    print(f"  ✓ Loaded from Consul: {key_upper} = ***")
                else:
                    print(f"  ✓ Loaded from Consul: {key_upper} = {value}")
        
        print(f"\n✓ Successfully loaded config from Consul")
        
        setattr(settings, "REDIS_HOST", 'localhost')  # Override Redis host for local dev
    
    except Exception as e:
        print(f"⚠ Warning: Failed to load config from Consul: {e}")
        print("  Falling back to .env values")
    
    return settings


# Global settings instance
settings = get_settings()