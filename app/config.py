from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(extra='ignore', env_file=".env", case_sensitive=True)
    
    DATABASE_URL: str = Field(default="postgresql://claim_user:claim_password@localhost:5432/claim_db")
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=10080)
    
    # Reverse Proxy Settings
    BEHIND_PROXY: bool = Field(default=True)
    
    # Game Settings
    AUTO_LOG_DISTANCE: float = Field(default=20.0)  # meters
    MANUAL_LOG_DISTANCE: float = Field(default=100.0)  # meters
    LOG_COOLDOWN: int = Field(default=300)  # seconds (5 minutes)
    CLAIM_DECAY_RATE: float = Field(default=0.01)  # per hour
    
    # Testing/Development Settings
    TESTING: bool = Field(default=False)  # Set to True to disable spatial features for testing
    
    def is_sqlite(self) -> bool:
        """Check if the configured database is SQLite"""
        return self.DATABASE_URL.startswith("sqlite")
    
    def is_postgresql(self) -> bool:
        """Check if the configured database is PostgreSQL"""
        return self.DATABASE_URL.startswith("postgresql")

settings = Settings()
