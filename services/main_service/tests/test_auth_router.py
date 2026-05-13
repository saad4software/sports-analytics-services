from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_register_proxies_to_auth_service(monkeypatch):
    monkeypatch.setattr(
        "src.auth.router.auth_client.proxy",
        AsyncMock(
            return_value={
                "success": True,
                "message": "ok",
                "data": {"id": 1, "username": "remote"},
            }
        ),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/auth/register",
            json={"username": "remote", "password": "longenough"},
        )
    assert r.status_code == 200
    assert r.json()["data"]["username"] == "remote"


@pytest.mark.asyncio
async def test_login_proxies_form_body(monkeypatch):
    mock = AsyncMock(
        return_value={
            "success": True,
            "data": {"access_token": "tok", "token_type": "bearer"},
        }
    )
    monkeypatch.setattr("src.auth.router.auth_client.proxy", mock)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/auth/login",
            data={"username": "u1", "password": "p1"},
        )
    assert r.status_code == 200
    mock.assert_awaited_once()
    call = mock.await_args
    assert call.kwargs["data"]["username"] == "u1"
    assert call.kwargs["data"]["password"] == "p1"
