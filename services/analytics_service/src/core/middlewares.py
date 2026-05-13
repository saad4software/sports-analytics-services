import json

from fastapi import Request, Response
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.models import IResponse

_DOCS_PATHS = frozenset({"/openapi.json", "/docs", "/redoc"})


class UnifiedResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in _DOCS_PATHS:
            return await call_next(request)

        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if response.status_code < 400 and "application/json" in content_type:
            body = b"".join([section async for section in response.body_iterator])
            if not body:
                return response
            try:
                data = json.loads(body.decode("utf-8"))
                if isinstance(data, dict) and "success" in data:
                    response.body_iterator = iterate_in_threadpool(iter([body]))
                    return response

                wrapped_data = IResponse(data=data).model_dump_json()
                headers = dict(response.headers)
                headers.pop("Content-Length", None)
                headers.pop("content-length", None)

                return Response(
                    content=wrapped_data,
                    status_code=response.status_code,
                    headers=headers,
                    media_type="application/json",
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                response.body_iterator = iterate_in_threadpool(iter([body]))
                return response

        return response
