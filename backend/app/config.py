from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Get the backend directory path (where .env file is located)
BACKEND_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./polymarket.db"
    
    # JWT Settings
    secret_key: str = "dev-secret-key-change-this-in-production-please-123"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # App Settings
    starting_balance: int = 10000  # Starting coins (100 coins = $1)
    
    class Config:
        env_file = str(BACKEND_DIR / ".env")
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

# Debug: Print secret key length on startup (not the actual key for security)
print(f"[Config] Loaded secret key (length: {len(settings.secret_key)})")

