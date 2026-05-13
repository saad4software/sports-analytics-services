from unittest.mock import AsyncMock

import pytest
from src.analytics import worker


def _video_row() -> dict:
    return {
        "id": 1,
        "user_id": 2,
        "stored_path": "/tmp/fake.mp4",
        "first_team_color": "red",
        "second_team_color": "white",
        "original_filename": "f.mp4",
    }


@pytest.mark.asyncio
async def test_process_video_sets_status_and_notification(monkeypatch):
    monkeypatch.setattr(
        worker.media_client, "get_video", AsyncMock(return_value=_video_row())
    )
    monkeypatch.setattr(worker.media_client, "bulk_create_frames", AsyncMock())
    monkeypatch.setattr(worker.media_client, "update_video_status", AsyncMock())

    notif_calls: list[dict] = []

    async def fake_notif(**kw):
        notif_calls.append(kw)

    monkeypatch.setattr(worker.notifications_client, "create_notification", fake_notif)

    monkeypatch.setattr(worker._processor, "iter_frames", lambda *a, **k: iter(()))

    await worker._process_video({"video_id": 1})

    status_calls = worker.media_client.update_video_status.await_args_list
    assert len(status_calls) == 2
    assert status_calls[0].args[0] == 1
    assert status_calls[0].kwargs == {
        "status": "processing",
        "ignore_missing": False,
    }
    assert status_calls[1].args[0] == 1
    assert status_calls[1].kwargs == {
        "status": "done",
        "error_message": None,
        "ignore_missing": True,
    }
    assert notif_calls and notif_calls[0]["notification_type"] == "processing_complete"
    assert notif_calls[0]["video_id"] == 1


@pytest.mark.asyncio
async def test_process_video_failed_status_and_notification(monkeypatch):
    row = _video_row()
    row["id"] = 3
    row["user_id"] = 4
    row["original_filename"] = "bad.mp4"
    monkeypatch.setattr(worker.media_client, "get_video", AsyncMock(return_value=row))
    monkeypatch.setattr(worker.media_client, "bulk_create_frames", AsyncMock())
    monkeypatch.setattr(worker.media_client, "update_video_status", AsyncMock())

    notif_calls: list[dict] = []

    async def fake_notif(**kw):
        notif_calls.append(kw)

    monkeypatch.setattr(worker.notifications_client, "create_notification", fake_notif)

    def boom(*_a, **_k):
        raise RuntimeError("processor boom")

    monkeypatch.setattr(worker._processor, "iter_frames", boom)

    await worker._process_video({"video_id": 3})

    status_calls = worker.media_client.update_video_status.await_args_list
    assert len(status_calls) == 2
    assert status_calls[0].kwargs["status"] == "processing"
    assert status_calls[1].kwargs["status"] == "failed"
    assert "processor boom" in (status_calls[1].kwargs.get("error_message") or "")
    assert notif_calls and notif_calls[0]["notification_type"] == "processing_failed"
    assert notif_calls[0]["video_id"] == 3
