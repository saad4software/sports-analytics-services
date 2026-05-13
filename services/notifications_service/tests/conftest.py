import pytest
import src.notifications.models  # noqa: F401
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
from src.notifications.router import router as notifications_router


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
async def session_factory_override(db_engine):
    factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return factory


@pytest.fixture
async def internal_http_client(monkeypatch, db_engine, session_factory_override):
    monkeypatch.setattr(config, "internal_api_key", "test-internal-key")

    async def override_get_session():
        async with session_factory_override() as s:
            yield s

    app = FastAPI()
    setup_exception_handlers(app)
    app.add_middleware(UnifiedResponseMiddleware)
    app.include_router(notifications_router)

    app.dependency_overrides[core_db.get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
