import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = False  # Always default to False; set DEBUG=true only in .env for dev
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # IMPORTANT: Set a strong random SECRET_KEY in .env — never use this default in production!
    SECRET_KEY: str = "CHANGE_ME_in_env_file_use_32char_random_string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Set DATABASE_URL in .env — no credentials in source code
    DATABASE_URL: str = "sqlite:///./ayucare.db"  # Safe SQLite fallback; override in .env

    GEMINI_API_KEY: Optional[str] = None  # Set via GEMINI_API_KEY in .env

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "AyuCare Care Alert"
    SMTP_FROM_EMAIL: str = ""
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_MOCK: bool = True  # True = log emails to Live Inspector (safe for demo); False = real SMTP

    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
