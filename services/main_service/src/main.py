from contextlib import asynccontextmanager

from db_core import (
    UnifiedResponseMiddleware,
    setup_exception_handlers,
    setup_logging,
)
from fastapi import FastAPI

from src.auth.router import router as auth_router
from src.clients.analytics_client import analytics_client
from src.clients.auth_client import auth_client
from src.clients.media_client import media_client
from src.clients.notifications_client import notifications_client
from src.core.config import config
from src.notifications.router import router as notifications_router
from src.videos.router import router as videos_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await media_client.aclose()
    await notifications_client.aclose()
    await auth_client.aclose()
    await analytics_client.aclose()


app = FastAPI(title=config.app_name, lifespan=lifespan)
setup_exception_handlers(app)
app.add_middleware(UnifiedResponseMiddleware, skip_paths=["/auth/login"])

app.include_router(auth_router)
app.include_router(videos_router)
app.include_router(notifications_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
