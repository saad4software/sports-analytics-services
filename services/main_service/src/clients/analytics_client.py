import asyncio
import logging

import httpx
from fastapi import HTTPException

from src.core.config import config

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = frozenset({502, 503, 504, 429})
_SUBMIT_MAX_ATTEMPTS = 3


def _submit_retryable(exc: HTTPException) -> bool:
    if exc.status_code in _RETRYABLE_STATUS:
        return True
    detail = str(exc.detail).lower()
    return exc.status_code == 502 and "unreachable" in detail


class AnalyticsClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=config.analytics_service_url, timeout=10.0
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _submit_job_once(self, video_id: int, access_token: str) -> dict:
        try:
            resp = await self._client.post(
                "/analytics/process",
                json={"video_id": video_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=502, detail=f"Analytics service unreachable: {e}"
            )
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("message", resp.text)
            except ValueError:
                detail = resp.text
            raise HTTPException(status_code=resp.status_code, detail=str(detail))
        payload = resp.json()
        if isinstance(payload, dict) and "data" in payload and "success" in payload:
            return payload["data"]
        return payload

    async def submit_job(self, video_id: int, access_token: str) -> dict:
        last: HTTPException | None = None
        for attempt in range(1, _SUBMIT_MAX_ATTEMPTS + 1):
            try:
                return await self._submit_job_once(video_id, access_token)
            except HTTPException as e:
                last = e
                if attempt == _SUBMIT_MAX_ATTEMPTS or not _submit_retryable(e):
                    raise
                delay = 0.35 * attempt
                logger.warning(
                    "Analytics enqueue attempt %d/%d failed for video_id=%s (%s); "
                    "retrying in %.1fs",
                    attempt,
                    _SUBMIT_MAX_ATTEMPTS,
                    video_id,
                    e.detail,
                    delay,
                )
                await asyncio.sleep(delay)
        raise last  # pragma: no cover


analytics_client = AnalyticsClient()
