import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    app_name: str = "Analytics Service"
    debug: bool = True

    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-jwt-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    queue_name: str = os.getenv("ANALYTICS_QUEUE", "sports:analytics:jobs")


config = Config()
