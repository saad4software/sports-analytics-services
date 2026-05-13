import pytest
from httpx import AsyncClient


def _h(key: str = "test-internal-key") -> dict[str, str]:
    return {"X-Internal-Key": key}


@pytest.mark.asyncio
async def test_internal_routes_reject_missing_key(internal_http_client: AsyncClient):
    r = await internal_http_client.get("/internal/videos/1")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_videos_create_get_list_and_status_update(
    internal_http_client: AsyncClient,
):
    create = await internal_http_client.post(
        "/internal/videos",
        json={
            "user_id": 42,
            "original_filename": "clip.mp4",
            "stored_path": "/tmp/clip.mp4",
            "first_team_color": "red",
            "second_team_color": "white",
        },
        headers=_h(),
    )
    assert create.status_code == 201
    vid = create.json()["data"]
    assert vid["status"] == "uploaded"

    listed = await internal_http_client.get(
        "/internal/videos", params={"user_id": 42}, headers=_h()
    )
    assert listed.status_code == 200
    assert [v["id"] for v in listed.json()["data"]] == [vid["id"]]

    patched = await internal_http_client.patch(
        f"/internal/videos/{vid['id']}/status",
        json={"status": "processing", "error_message": None},
        headers=_h(),
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["status"] == "processing"


@pytest.mark.asyncio
async def test_videos_same_colors_rejected(internal_http_client: AsyncClient):
    bad = await internal_http_client.post(
        "/internal/videos",
        json={
            "user_id": 1,
            "original_filename": "a.mp4",
            "stored_path": "/tmp/a.mp4",
            "first_team_color": "red",
            "second_team_color": "red",
        },
        headers=_h(),
    )
    assert bad.status_code == 400


@pytest.mark.asyncio
async def test_frames_bulk_create_and_list(internal_http_client: AsyncClient):
    create = await internal_http_client.post(
        "/internal/videos",
        json={
            "user_id": 7,
            "original_filename": "v.mp4",
            "stored_path": "/tmp/v.mp4",
            "first_team_color": "red",
            "second_team_color": "white",
        },
        headers=_h(),
    )
    vid = create.json()["data"]["id"]

    bulk = await internal_http_client.post(
        "/internal/frames/bulk",
        json={
            "video_id": vid,
            "frames": [
                {
                    "frame_number": i,
                    "time": "2026-05-12T00:00:00+00:00",
                    "first_team_count": 0,
                    "second_team_count": 0,
                    "referee_count": 0,
                }
                for i in (1, 2, 3)
            ],
        },
        headers=_h(),
    )
    assert bulk.status_code == 200
    assert bulk.json()["data"]["inserted"] == 3

    listed = await internal_http_client.get(
        "/internal/frames",
        params={"video_id": vid, "limit": 2, "offset": 1},
        headers=_h(),
    )
    assert listed.status_code == 200
    nums = [f["frame_number"] for f in listed.json()["data"]]
    assert nums == [2, 3]
