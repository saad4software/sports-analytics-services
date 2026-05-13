from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.analytics.router import router as analytics_router
from src.core.exceptions import setup_exception_handlers
from src.core.middlewares import UnifiedResponseMiddleware


@pytest.fixture
def analytics_app():
    app = FastAPI()
    setup_exception_handlers(app)
    app.add_middleware(UnifiedResponseMiddleware)
    app.include_router(analytics_router)
    return app


@pytest.mark.asyncio
async def test_process_accepts_job(make_token, monkeypatch, analytics_app):
    mock_enqueue = AsyncMock()
    monkeypatch.setattr("src.analytics.router.enqueue_job", mock_enqueue)

    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/analytics/process",
            json={"video_id": 42},
            headers={"Authorization": f"Bearer {make_token(user_id=9)}"},
        )

    assert r.status_code == 202
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["queued"] is True
    assert data["video_id"] == 42

    mock_enqueue.assert_awaited_once()
    job = mock_enqueue.await_args.args[0]
    assert job == {"video_id": 42, "requested_by": 9}


@pytest.mark.asyncio
async def test_process_requires_auth(analytics_app):
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/analytics/process", json={"video_id": 1})
    assert r.status_code == 401
