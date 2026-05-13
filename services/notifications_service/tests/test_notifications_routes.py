import pytest
from httpx import AsyncClient
from src.notifications.models import NotificationCreate
from src.notifications.service import NotificationService


@pytest.mark.asyncio
async def test_internal_routes_reject_missing_key(internal_http_client: AsyncClient):
    r = await internal_http_client.get(
        "/internal/notifications", params={"user_id": 1}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_notifications_returns_persisted_rows(
    internal_http_client: AsyncClient, session_factory_override
):
    async with session_factory_override() as session:
        svc = NotificationService(session)
        await svc.create(
            NotificationCreate(
                user_id=42,
                video_id=7,
                type="processing_complete",
                message="hello",
            )
        )

    r = await internal_http_client.get(
        "/internal/notifications",
        params={"user_id": 42},
        headers={"X-Internal-Key": "test-internal-key"},
    )
    assert r.status_code == 200
    rows = r.json()["data"]
    assert [row["message"] for row in rows] == ["hello"]


@pytest.mark.asyncio
async def test_create_notification_persists_row(internal_http_client: AsyncClient):
    r = await internal_http_client.post(
        "/internal/notifications",
        headers={"X-Internal-Key": "test-internal-key"},
        json={
            "user_id": 99,
            "video_id": 10,
            "type": "processing_complete",
            "message": "Video 'g.mp4' has finished processing.",
        },
    )
    assert r.status_code == 201
    body = r.json()["data"]
    assert body["user_id"] == 99
    assert body["video_id"] == 10
    assert body["type"] == "processing_complete"


@pytest.mark.asyncio
async def test_create_notification_rejects_missing_key(internal_http_client: AsyncClient):
    r = await internal_http_client.post(
        "/internal/notifications",
        json={
            "user_id": 1,
            "video_id": 2,
            "type": "processing_complete",
            "message": "x",
        },
    )
    assert r.status_code == 401
