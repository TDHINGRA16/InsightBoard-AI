"""
Application configuration using pydantic-settings.
Loads environment variables from .env file.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "InsightBoard"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Groq LLM
    GROQ_API_KEY: str
    GROQ_MODEL: str = "mixtral-8x7b-32768"

    # Supabase (optional for local dev)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_JWT_SECRET: str = "dev-secret-key"

    # CORS - stored as comma-separated string, parsed as list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = [".txt", ".pdf"]

    # Cache TTL (seconds)
    ANALYSIS_CACHE_TTL: int = 86400  # 24 hours

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        """Convert postgres:// to postgresql:// for SQLAlchemy compatibility."""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS as list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application configuration instance
    """
    return Settings()


settings = get_settings()

