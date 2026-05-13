import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_and_wrong_password(auth_http_client: AsyncClient):
    r = await auth_http_client.post(
        "/auth/register",
        json={"username": "reguser", "password": "password-ok"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"]["username"] == "reguser"

    form = {"username": "reguser", "password": "wrong-pass"}
    bad = await auth_http_client.post("/auth/login", data=form)
    assert bad.status_code == 401

    ok = await auth_http_client.post(
        "/auth/login", data={"username": "reguser", "password": "password-ok"}
    )
    assert ok.status_code == 200
    token_body = ok.json()
    # `/auth/login` bypasses UnifiedResponseMiddleware (OAuth2 compatibility).
    assert "access_token" in token_body
    assert token_body.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_login_unknown_user(auth_http_client: AsyncClient):
    r = await auth_http_client.post(
        "/auth/login",
        data={"username": "nouser", "password": "password-ok"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_username(auth_http_client: AsyncClient):
    payload = {"username": "dupuser", "password": "password-ok"}
    first = await auth_http_client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = await auth_http_client.post("/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_register_validation_short_password(auth_http_client: AsyncClient):
    r = await auth_http_client.post(
        "/auth/register",
        json={"username": "validname", "password": "short"},
    )
    # RequestValidationError is mapped to HTTP 400 by the global handler.
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_login_validation_short_username(auth_http_client: AsyncClient):
    r = await auth_http_client.post(
        "/auth/login",
        data={"username": "ab", "password": "password-ok"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_health_wrapped(auth_http_client: AsyncClient):
    r = await auth_http_client.get("/health")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ok"
