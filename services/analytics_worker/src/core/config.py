import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    """Worker config: Redis queue, media_service, notifications_service (HTTP)."""

    debug: bool = True

    # ``DB_SERVICE_URL`` is an alias for ``MEDIA_SERVICE_URL``.
    media_service_url: str = os.getenv(
        "MEDIA_SERVICE_URL",
        os.getenv("DB_SERVICE_URL", "http://localhost:8004"),
    )
    notifications_service_url: str = os.getenv(
        "NOTIFICATIONS_SERVICE_URL", "http://localhost:8005"
    )
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-internal-key")

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    queue_name: str = os.getenv("ANALYTICS_QUEUE", "sports:analytics:jobs")

    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "yolo26x.pt")


config = Config()
