import pytest
import src.frames.models  # noqa: F401
import src.videos.models  # noqa: F401
from db_core import UnifiedResponseMiddleware, setup_exception_handlers
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from src.core import db as core_db
from src.core.config import config
from src.frames.router import router as frames_router
from src.videos.router import router as videos_router


@pytest.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        yield s


@pytest.fixture
async def internal_http_client(monkeypatch, db_engine):
    monkeypatch.setattr(config, "internal_api_key", "test-internal-key")

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_session():
        async with session_factory() as s:
            yield s

    app = FastAPI()
    setup_exception_handlers(app)
    app.add_middleware(UnifiedResponseMiddleware)
    app.include_router(videos_router)
    app.include_router(frames_router)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.dependency_overrides[core_db.get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
