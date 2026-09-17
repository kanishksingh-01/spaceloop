import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    APP_NAME: str = "NIRIKSHAK"
    APP_VERSION: str = "0.1.0-mvp"

    # API Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Security & JWT
    SECRET_KEY: str = "dev_insecure_secret_key_change_in_production_32bytesmin"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours for demo

    # Database Configuration (PostgreSQL default; fallback to SQLite for local dev if needed)
    DATABASE_URL: str = "postgresql+asyncpg://nirikshak:nirikshak_dev_pass@db:5432/nirikshak"
    DATABASE_SYNC_URL: str = "postgresql+psycopg://nirikshak:nirikshak_dev_pass@db:5432/nirikshak"

    # Risk Scoring Policy Weights (4 deterministic signals summing to 1.0)
    WEIGHT_IDENTITY: float = 0.25
    WEIGHT_DEVICE: float = 0.25
    WEIGHT_SENSITIVITY: float = 0.25
    WEIGHT_BEHAVIOR: float = 0.25

    # Risk Classification Thresholds
    RISK_THRESHOLD_MODERATE: float = 31.0
    RISK_THRESHOLD_HIGH: float = 61.0
    RISK_THRESHOLD_CRITICAL: float = 81.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
