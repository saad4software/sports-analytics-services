from typing import Annotated

from db_core import make_session_dependency, make_session_factory
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import config

session_factory = make_session_factory(
    config.database_url,
    pool_size=config.db_pool_size,
    max_overflow=config.db_max_overflow,
    pool_recycle=config.db_pool_recycle_seconds,
    pool_pre_ping=config.db_pool_pre_ping,
)

get_session = make_session_dependency(session_factory)
SessionDep = Annotated[AsyncSession, Depends(get_session)]
