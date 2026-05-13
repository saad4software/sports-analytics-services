from contextlib import asynccontextmanager

from db_core import (
    UnifiedResponseMiddleware,
    setup_exception_handlers,
    setup_logging,
)
from fastapi import FastAPI

import src.notifications.models  # noqa: F401  (register table)
from src.core.config import config
from src.core.db import session_factory
from src.notifications.router import router as notifications_router

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
app.include_router(notifications_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
