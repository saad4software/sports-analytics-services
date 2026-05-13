import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Config(BaseSettings):
    """media_service config; owns ``video_file`` and ``frame`` tables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Media Service"
    debug: bool = True

    database_url: str = os.getenv(
        "MEDIA_DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/sports_media",
        ),
    )
    db_pool_size: int = 10
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 1800
    db_pool_pre_ping: bool = True

    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-internal-key")


config = Config()
