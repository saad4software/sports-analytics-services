import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Config(BaseSettings):
    """auth_service config.

    Owns its own database (``database_url``) — there is no DB service to
    talk to anymore; ``users`` lives here.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Auth Service"
    debug: bool = True

    # Per-service database. AUTH_DATABASE_URL is preferred so the three
    # services can each point at their own database without colliding;
    # DATABASE_URL is accepted as a fallback for single-DB local setups.
    database_url: str = os.getenv(
        "AUTH_DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/sports_auth",
        ),
    )

    db_pool_size: int = 10
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 1800
    db_pool_pre_ping: bool = True

    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-jwt-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_exp_minutes: int = int(os.getenv("JWT_ACCESS_EXP_MINUTES", "60"))


config = Config()
