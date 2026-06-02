from typing import Annotated

from pydantic_settings import BaseSettings, NoDecode
from pydantic import ConfigDict, field_validator

class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "E-commerce API"
    DEBUG: bool = False
    ENABLE_RATE_LIMITS: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int 
    SECRET_KEY: str
    ALGORITHM: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode]  # frontend URL

    model_config = ConfigDict(env_file=".env")

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Allow boolean-like values and environment labels from .env/CI."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod"}:
                return False
            if normalized in {"development", "dev"}:
                return True
        return value

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value):
        """Allow comma-separated string from .env"""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value

settings = Settings()
