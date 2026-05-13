import pytest
from src.clients.auth_client import AuthClient


@pytest.mark.asyncio
async def test_proxy_rejects_both_json_and_data():
    client = AuthClient()
    try:
        with pytest.raises(ValueError):
            await client.proxy("/auth/x", json=None, data=None)
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_proxy_rejects_neither_json_nor_data():
    client = AuthClient()
    try:
        with pytest.raises(ValueError):
            await client.proxy(
                "/auth/x",
                json={"a": 1},
                data={"b": 2},
            )
    finally:
        await client.aclose()
