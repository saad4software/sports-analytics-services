import pytest
from fastapi import HTTPException
from src.clients.analytics_client import AnalyticsClient


@pytest.mark.asyncio
async def test_submit_job_retries_on_transient_502(monkeypatch):
    client = AnalyticsClient()
    try:
        attempts = {"n": 0}

        async def once(self, video_id, access_token):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise HTTPException(
                    status_code=502, detail="Analytics service unreachable: test"
                )
            return {"queued": True, "video_id": video_id}

        monkeypatch.setattr(AnalyticsClient, "_submit_job_once", once)
        out = await client.submit_job(42, "token")
        assert out["queued"] is True
        assert attempts["n"] == 3
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_submit_job_does_not_retry_on_401(monkeypatch):
    client = AnalyticsClient()
    try:
        attempts = {"n": 0}

        async def once(self, video_id, access_token):
            attempts["n"] += 1
            raise HTTPException(status_code=401, detail="unauthorized")

        monkeypatch.setattr(AnalyticsClient, "_submit_job_once", once)
        with pytest.raises(HTTPException) as exc_info:
            await client.submit_job(1, "t")
        assert exc_info.value.status_code == 401
        assert attempts["n"] == 1
    finally:
        await client.aclose()
