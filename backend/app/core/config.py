"""
Mind Application Configuration
Loads settings from environment variables and .env with strict type validation.
"""
from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Core Application
    APP_NAME: str = "Mind"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    PRODUCT_DISPLAY_NAME: str = "Mind"
    PRODUCT_TAGLINE: str = "Intelligence for Better Learning"

    # Security & Sessions
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-min-32-chars-long"
    SESSION_COOKIE_NAME: str = "mind_session"
    SESSION_MAX_AGE_SECONDS: int = 86400  # 24 hours
    SECURE_COOKIES: bool = False
    SAME_SITE: str = "lax"
    PASSWORD_HASH_ALGORITHM: str = "argon2id"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./mind_dev.db"
    DATABASE_ECHO: bool = False

    # Queue / Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage (local or s3)
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_PATH: str = "./local_storage"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "mind-assets"
    AWS_S3_ENDPOINT_URL: Optional[str] = None

    # AI Gateway
    AI_PROVIDER: str = "mock"  # 'mock' or 'gemini'
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_FLASH_MODEL: str = "gemini-1.5-flash"
    GEMINI_PRO_MODEL: str = "gemini-1.5-pro"

    # Email & Notifications
    EMAIL_BACKEND: str = "console"  # 'console', 'mailpit', 'smtp', 'resend'
    MAILPIT_HOST: str = "localhost"
    MAILPIT_PORT: int = 1025
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "no-reply@mindlearning.local"

    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []


settings = Settings()

