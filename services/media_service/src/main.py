from contextlib import asynccontextmanager

from db_core import (
    UnifiedResponseMiddleware,
    setup_exception_handlers,
    setup_logging,
)
from fastapi import FastAPI

import src.frames.models  # noqa: F401
import src.videos.models  # noqa: F401  (register tables with SQLModel.metadata)
from src.core.config import config
from src.core.db import session_factory
from src.frames.router import router as frames_router
from src.videos.router import router as videos_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await session_factory.dispose()


app = FastAPI(title=config.app_name, lifespan=lifespan)
setup_exception_handlers(app)
app.add_middleware(UnifiedResponseMiddleware)
app.include_router(videos_router)
app.include_router(frames_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
