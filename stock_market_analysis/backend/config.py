"""
QuantNova AI - Core Configuration & Settings Management
Loads configuration from environment variables (.env) with production defaults.
Resilient against missing pydantic_settings.
"""

import os
from pathlib import Path
from typing import List

# Base Directory of backend
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
ENV_FILE = ROOT_DIR / ".env"

# Load .env file if present
if ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE)
    except ImportError:
        # Simple fallback .env parser
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field

    class Settings(BaseSettings):
        app_env: str = Field(default="development", alias="APP_ENV")
        debug: bool = Field(default=True, alias="DEBUG")
        port: int = Field(default=8000, alias="PORT")
        host: str = Field(default="0.0.0.0", alias="HOST")

        # Database URL
        database_url: str = Field(
            default="postgresql+psycopg://postgres:postgres@localhost:5432/quantnova_db",
            alias="DATABASE_URL"
        )

        db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
        db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
        db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
        db_pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")

        cors_origins: str = Field(
            default="http://localhost:5173,http://localhost:3000,https://quant-nova-ai-rprt.vercel.app",
            alias="CORS_ORIGINS"
        )

        @property
        def cors_origin_list(self) -> List[str]:
            return [orig.strip() for orig in self.cors_origins.split(",") if orig.strip()]

        @property
        def cleaned_database_url(self) -> str:
            url = (self.database_url or "").strip()
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url

        class Config:
            env_file = str(ENV_FILE)
            env_file_encoding = "utf-8"
            extra = "ignore"

    settings = Settings()

except ImportError:
    # Graceful fallback when pydantic_settings is not yet installed
    class FallbackSettings:
        def __init__(self):
            self.app_env = os.getenv("APP_ENV", "development")
            self.debug = os.getenv("DEBUG", "True").lower() in ("true", "1")
            self.port = int(os.getenv("PORT", "8000"))
            self.host = os.getenv("HOST", "0.0.0.0")
            self.database_url = os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://postgres:postgres@localhost:5432/quantnova_db"
            )
            self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
            self.db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
            self.db_pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
            self.db_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
            self.cors_origins = os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://localhost:3000,https://quant-nova-ai-rprt.vercel.app"
            )

        @property
        def cors_origin_list(self) -> List[str]:
            return [orig.strip() for orig in self.cors_origins.split(",") if orig.strip()]

        @property
        def cleaned_database_url(self) -> str:
            url = (self.database_url or "").strip()
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url

    settings = FallbackSettings()
