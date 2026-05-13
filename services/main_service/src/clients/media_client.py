"""HTTP client for media_service internal video and frame routes."""

from typing import Any

import httpx
from fastapi import HTTPException, status

from src.core.config import config


class MediaClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=config.media_service_url,
            headers={"X-Internal-Key": config.internal_api_key},
            timeout=10.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _unwrap(response: httpx.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from media service",
            )
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    def _check(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("message", resp.text)
            except ValueError:
                detail = resp.text
            raise HTTPException(
                status_code=resp.status_code if resp.status_code < 500 else 502,
                detail=str(detail),
            )

    async def create_video(
        self,
        user_id: int,
        original_filename: str,
        stored_path: str,
        first_team_color: str,
        second_team_color: str,
    ) -> dict:
        resp = await self._client.post(
            "/internal/videos",
            json={
                "user_id": user_id,
                "original_filename": original_filename,
                "stored_path": stored_path,
                "first_team_color": first_team_color,
                "second_team_color": second_team_color,
            },
        )
        self._check(resp)
        return self._unwrap(resp)

    async def list_videos(self, user_id: int) -> list[dict]:
        resp = await self._client.get(
            "/internal/videos", params={"user_id": user_id}
        )
        self._check(resp)
        return self._unwrap(resp)

    async def get_video(self, video_id: int) -> dict:
        resp = await self._client.get(f"/internal/videos/{video_id}")
        self._check(resp)
        return self._unwrap(resp)

    async def update_video_status(
        self,
        video_id: int,
        *,
        status: str,
        error_message: str | None = None,
    ) -> dict:
        resp = await self._client.patch(
            f"/internal/videos/{video_id}/status",
            json={"status": status, "error_message": error_message},
        )
        self._check(resp)
        return self._unwrap(resp)

    async def list_frames(
        self, video_id: int, limit: int, offset: int
    ) -> list[dict]:
        resp = await self._client.get(
            "/internal/frames",
            params={"video_id": video_id, "limit": limit, "offset": offset},
        )
        self._check(resp)
        return self._unwrap(resp)


media_client = MediaClient()
