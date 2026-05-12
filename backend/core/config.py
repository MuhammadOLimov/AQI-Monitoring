"""
Core configuration module using Pydantic Settings.
Reads from environment variables and .env file.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Air Pollution Monitor"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/air_pollution_db"
    DATABASE_SYNC_URL: str = "postgresql://postgres:password@localhost:5432/air_pollution_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if not v:
            return v
        # Render/Heroku provide URLs starting with postgres://
        # but asyncpg requires postgresql+asyncpg://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300

    # OpenWeatherMap
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "http://api.openweathermap.org/data/2.5/air_pollution"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    ALERT_EMAIL_FROM: str = ""
    ALERT_EMAIL_TO: str = ""
    EMAIL_ALERTS_ENABLED: bool = False

    # Alert thresholds
    AQI_ALERT_THRESHOLD: int = 100
    AQI_CRITICAL_THRESHOLD: int = 200

    # Data collection
    DATA_FETCH_INTERVAL: int = 1800
    AUTO_FETCH_CITIES: str = "Tashkent,Samarkand,Bukhara,Fergana,Andijan,Namangan,Navoiy,Urgench,Nukus,Qarshi,Termiz,Jizzax,Guliston,Olmaliq,Chirchiq,Angren,Bekobod,Margilan,Kokand,Denov,Shahrisabz,Zarafshon,Xiva"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    CORS_ALLOW_ALL: bool = True

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_EMAIL: str = "admin@localhost"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def auto_fetch_cities_list(self) -> List[str]:
        return [c.strip() for c in self.AUTO_FETCH_CITIES.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
