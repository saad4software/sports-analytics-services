"""HTTP client for media_service (videos, frames bulk upload)."""

from typing import Any

import httpx

from src.core.config import config


class MediaClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=config.media_service_url,
            headers={"X-Internal-Key": config.internal_api_key},
            timeout=30.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _unwrap(resp: httpx.Response) -> Any:
        payload = resp.json()
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    async def get_video(self, video_id: int) -> dict:
        resp = await self._client.get(f"/internal/videos/{video_id}")
        resp.raise_for_status()
        return self._unwrap(resp)

    async def bulk_create_frames(self, video_id: int, frames: list[dict]) -> dict:
        resp = await self._client.post(
            "/internal/frames/bulk",
            json={"video_id": video_id, "frames": frames},
        )
        resp.raise_for_status()
        return self._unwrap(resp)

    async def update_video_status(
        self,
        video_id: int,
        *,
        status: str,
        error_message: str | None = None,
        ignore_missing: bool = False,
    ) -> None:
        resp = await self._client.patch(
            f"/internal/videos/{video_id}/status",
            json={"status": status, "error_message": error_message},
        )
        if ignore_missing and resp.status_code == 404:
            return
        resp.raise_for_status()


media_client = MediaClient()
