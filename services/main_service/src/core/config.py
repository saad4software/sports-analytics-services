import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    app_name: str = "Main Service"
    debug: bool = True

    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8002")
    media_service_url: str = os.getenv(
        "MEDIA_SERVICE_URL",
        os.getenv("DB_SERVICE_URL", "http://localhost:8004"),
    )
    notifications_service_url: str = os.getenv(
        "NOTIFICATIONS_SERVICE_URL", "http://localhost:8005"
    )
    analytics_service_url: str = os.getenv(
        "ANALYTICS_SERVICE_URL", "http://localhost:8003"
    )
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-internal-key")

    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-jwt-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")


config = Config()
