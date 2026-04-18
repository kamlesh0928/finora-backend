"""
Application configuration using Pydantic Settings.
Loads from environment variables / .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Finora API"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Database (NeonDB PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@host/dbname"

    # JWT Auth
    JWT_SECRET: str = "change-me-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google Gemini AI
    GOOGLE_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Rate Limiting (free tier protection)
    GEMINI_RATE_LIMIT_PER_MINUTE: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
