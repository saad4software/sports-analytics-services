from contextlib import asynccontextmanager

from db_core import (
    UnifiedResponseMiddleware,
    setup_exception_handlers,
    setup_logging,
)
from fastapi import FastAPI

import src.auth.models  # noqa: F401  (register table with SQLModel.metadata)
from src.auth.router import router as auth_router
from src.core.config import config
from src.core.db import session_factory

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await session_factory.dispose()


app = FastAPI(title=config.app_name, lifespan=lifespan)
setup_exception_handlers(app)
# /auth/login must stay raw so OAuth2 form clients see {access_token,...}.
app.add_middleware(UnifiedResponseMiddleware, skip_paths=["/auth/login"])
app.include_router(auth_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
