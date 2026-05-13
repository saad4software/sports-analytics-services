import json
from typing import Iterable

from fastapi import Request, Response
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from db_core.models import IResponse


class UnifiedResponseMiddleware(BaseHTTPMiddleware):
    """Wrap successful JSON responses in ``{success, message, data}``.

    Routes that already produce the envelope (or that must stay raw for
    interop, like OAuth2 ``/auth/login``) can opt out via ``skip_paths``.
    """

    def __init__(self, app, skip_paths: Iterable[str] = ()):
        super().__init__(app)
        # OpenAPI/docs routes are always skipped so Swagger stays usable.
        self._skip = frozenset(
            {"/openapi.json", "/docs", "/redoc", *skip_paths}
        )

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self._skip:
            return await call_next(request)

        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if response.status_code >= 400 or "application/json" not in content_type:
            return response

        body = b"".join([section async for section in response.body_iterator])
        if not body:
            return response
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            response.body_iterator = iterate_in_threadpool(iter([body]))
            return response

        if isinstance(data, dict) and "success" in data:
            response.body_iterator = iterate_in_threadpool(iter([body]))
            return response

        wrapped = IResponse(data=data).model_dump_json()
        headers = dict(response.headers)
        headers.pop("Content-Length", None)
        headers.pop("content-length", None)
        return Response(
            content=wrapped,
            status_code=response.status_code,
            headers=headers,
            media_type="application/json",
        )
