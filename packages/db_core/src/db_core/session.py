"""Async SQLModel engine + session factory helpers.

Every service owns its own database; this module just centralises the
boilerplate of constructing an async engine, a sessionmaker, and a
FastAPI dependency that yields a session per request. Models and Alembic
projects stay in each service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Callable

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def make_engine(
    url: str,
    *,
    pool_size: int = 10,
    max_overflow: int = 10,
    pool_recycle: int = 1800,
    pool_pre_ping: bool = True,
) -> AsyncEngine:
    """Create an async engine with sensible defaults; SQLite skips pool args."""
    if _is_sqlite(url):
        return create_async_engine(url, connect_args={"check_same_thread": False})
    return create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
    )


@dataclass(slots=True)
class SessionFactory:
    """Holds the engine + sessionmaker pair owned by a single service."""

    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]

    async def dispose(self) -> None:
        await self.engine.dispose()


def make_session_factory(url: str, **engine_kwargs) -> SessionFactory:
    engine = make_engine(url, **engine_kwargs)
    sessionmaker = async_sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )
    return SessionFactory(engine=engine, sessionmaker=sessionmaker)


def make_session_dependency(
    factory: SessionFactory,
) -> Callable[..., AsyncIterator[AsyncSession]]:
    """Return a ``get_session`` callable suitable for ``Depends``."""

    async def _get_session() -> AsyncIterator[AsyncSession]:
        async with factory.sessionmaker() as session:
            try:
                yield session
            finally:
                await session.close()

    return _get_session
