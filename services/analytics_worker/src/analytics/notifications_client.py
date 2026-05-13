"""HTTP client for notifications_service internal create route."""

from typing import Any

import httpx

from src.core.config import config


class NotificationsClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=config.notifications_service_url,
            headers={"X-Internal-Key": config.internal_api_key},
            timeout=10.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _unwrap(resp: httpx.Response) -> Any:
        payload = resp.json()
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    async def create_notification(
        self,
        *,
        user_id: int,
        video_id: int,
        notification_type: str,
        message: str,
    ) -> dict:
        resp = await self._client.post(
            "/internal/notifications",
            json={
                "user_id": user_id,
                "video_id": video_id,
                "type": notification_type,
                "message": message,
            },
        )
        resp.raise_for_status()
        return self._unwrap(resp)


notifications_client = NotificationsClient()
