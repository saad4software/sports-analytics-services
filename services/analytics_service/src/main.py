from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.analytics import queue
from src.analytics.router import router as analytics_router
from src.core.config import config
from src.core.exceptions import setup_exception_handlers
from src.core.logging import setup_logging
from src.core.middlewares import UnifiedResponseMiddleware

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await queue.aclose()


app = FastAPI(title=config.app_name, lifespan=lifespan)
setup_exception_handlers(app)
app.add_middleware(UnifiedResponseMiddleware)
app.include_router(analytics_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
