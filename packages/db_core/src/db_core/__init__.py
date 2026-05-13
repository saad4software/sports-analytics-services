"""Shared library for the sports-analytics services.

Provides the small set of plumbing that every Python service in this repo
needs but does not justify a runtime process:

- A typed async SQLModel session helper for each service's database.
- The `IResponse` envelope + middleware that wrap successful JSON responses.
- A common exception handler so HTTP errors render with the same shape.
- Internal-API-key guard for service-to-service routes.
- JWT verification + a `CurrentUser` model shared by Main and the
  downstream services that verify access tokens locally.
- Structured logging configuration.

Migrations are NOT shipped here. Each service owns its own SQLModel models
and its own Alembic project; this library only provides the engine factory
and session dependency they wire into FastAPI.
"""

from db_core.exceptions import setup_exception_handlers
from db_core.jwt_auth import CurrentUser, decode_access_token, make_oauth2_scheme
from db_core.logging import setup_logging
from db_core.middlewares import UnifiedResponseMiddleware
from db_core.models import IResponse
from db_core.security import require_internal_key
from db_core.session import (
    SessionFactory,
    make_engine,
    make_session_dependency,
    make_session_factory,
)

__all__ = [
    "CurrentUser",
    "IResponse",
    "SessionFactory",
    "UnifiedResponseMiddleware",
    "decode_access_token",
    "make_engine",
    "make_oauth2_scheme",
    "make_session_dependency",
    "make_session_factory",
    "require_internal_key",
    "setup_exception_handlers",
    "setup_logging",
]
