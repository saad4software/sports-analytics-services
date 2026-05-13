from datetime import UTC, datetime, timedelta
from io import BytesIO
from unittest.mock import AsyncMock

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from src.core.config import config
from src.main import app


def _video_row(
    *,
    vid: int = 1,
    user_id: int = 1,
    stored_path: str = "/tmp/x.mp4",
    status: str = "uploaded",
) -> dict:
    return {
        "id": vid,
        "user_id": user_id,
        "original_filename": "clip.mp4",
        "stored_path": stored_path,
        "first_team_color": "red",
        "second_team_color": "white",
        "status": status,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "error_message": None,
    }


@pytest.mark.asyncio
async def test_upload_rejects_same_team_colors(make_token):
    token = make_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("a.mp4", BytesIO(b"x"), "video/mp4")}
        data = {"first_team_color": "red", "second_team_color": "red"}
        r = await client.post(
            "/videos",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_upload_returns_uploaded_when_analytics_enqueue_succeeds(
    make_token, monkeypatch, tmp_path
):
    # Status stays ``uploaded`` on the create response; analytics_worker
    # flips it to ``processing`` after dequeuing (see README "Worker-owned
    # lifecycle updates"). The router only enqueues; it must not call
    # update_video_status itself.
    monkeypatch.setattr(config, "upload_dir", str(tmp_path))
    monkeypatch.setattr(config, "public_base_url", "http://public.example")

    created = _video_row(vid=9, user_id=1)

    monkeypatch.setattr(
        "src.videos.router.media_client.create_video",
        AsyncMock(return_value=created),
    )
    submit_job = AsyncMock(return_value={"queued": True})
    monkeypatch.setattr(
        "src.videos.router.analytics_client.submit_job",
        submit_job,
    )

    token = make_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("a.mp4", BytesIO(b"chunk"), "video/mp4")}
        data = {"first_team_color": "red", "second_team_color": "white"}
        r = await client.post(
            "/videos",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"]["id"] == 9
    assert body["data"]["status"] == "uploaded"
    submit_job.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_persists_even_when_analytics_fails(
    make_token, monkeypatch, tmp_path
):
    monkeypatch.setattr(config, "upload_dir", str(tmp_path))
    monkeypatch.setattr(config, "public_base_url", "http://public.example")

    created = _video_row(vid=7, user_id=1)

    monkeypatch.setattr(
        "src.videos.router.media_client.create_video",
        AsyncMock(return_value=created),
    )

    async def boom(*_a, **_k):
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="analytics down")

    monkeypatch.setattr("src.videos.router.analytics_client.submit_job", boom)

    token = make_token()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("a.mp4", BytesIO(b"chunk"), "video/mp4")}
        data = {"first_team_color": "red", "second_team_color": "white"}
        r = await client.post(
            "/videos",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"]["id"] == 7
    assert body["data"]["status"] == "uploaded"


@pytest.mark.asyncio
async def test_get_video_forbidden_for_other_user(make_token, monkeypatch):
    monkeypatch.setattr(config, "public_base_url", "http://public.example")
    monkeypatch.setattr(
        "src.videos.router.media_client.get_video",
        AsyncMock(return_value=_video_row(user_id=99)),
    )

    token = make_token(user_id=1)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/videos/1",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_stream_media_missing_file(make_token, monkeypatch, tmp_path):
    missing = tmp_path / "nope.mp4"
    monkeypatch.setattr(
        "src.videos.router.media_client.get_video",
        AsyncMock(
            return_value=_video_row(
                vid=3,
                user_id=1,
                stored_path=str(missing),
            )
        ),
    )

    token = make_token(user_id=1)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/videos/3/media",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_videos_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/videos")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_type_rejected(jwt_secret):
    now = datetime.now(UTC)
    bad = jwt.encode(
        {
            "sub": "1",
            "uid": 1,
            "username": "x",
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=60)).timestamp()),
        },
        jwt_secret,
        algorithm="HS256",
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/videos", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401
