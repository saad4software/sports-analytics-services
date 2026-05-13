"""HTTP client for notifications_service (internal list + create from worker)."""

from typing import Any

import httpx
from fastapi import HTTPException, status

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
    def _unwrap(response: httpx.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from notifications service",
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

    async def list_notifications(self, user_id: int) -> list[dict]:
        resp = await self._client.get(
            "/internal/notifications", params={"user_id": user_id}
        )
        self._check(resp)
        return self._unwrap(resp)


notifications_client = NotificationsClient()
