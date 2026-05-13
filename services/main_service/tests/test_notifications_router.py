from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_list_notifications_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/notifications")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_notifications_returns_upstream_payload(make_token, monkeypatch):
    monkeypatch.setattr(
        "src.notifications.router.notifications_client.list_notifications",
        AsyncMock(return_value=[{"id": 1, "message": "hi"}]),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/notifications",
            headers={"Authorization": f"Bearer {make_token()}"},
        )
    assert r.status_code == 200
    assert r.json()["data"] == [{"id": 1, "message": "hi"}]
