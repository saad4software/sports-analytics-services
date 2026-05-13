import httpx
from fastapi import HTTPException

from src.core.config import config


class AuthClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=config.auth_service_url, timeout=10.0
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def proxy(
        self,
        path: str,
        *,
        json: dict | None = None,
        data: dict | None = None,
    ) -> dict:
        if (json is None) == (data is None):
            raise ValueError("Provide exactly one of json= or data=")
        try:
            if json is not None:
                resp = await self._client.post(path, json=json)
            else:
                resp = await self._client.post(path, data=data)
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Auth service unreachable: {e}")
        try:
            payload = resp.json()
        except ValueError:
            payload = {"message": resp.text}
        if resp.status_code >= 400:
            message = payload.get("message") if isinstance(payload, dict) else str(payload)
            raise HTTPException(status_code=resp.status_code, detail=message or "Auth error")
        # Auth service wraps JSON (except /auth/login); unwrap IResponse when present.
        if isinstance(payload, dict) and "data" in payload and "success" in payload:
            return payload["data"]
        return payload


auth_client = AuthClient()
