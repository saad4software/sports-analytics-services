"""Producer-side Redis enqueue for analytics jobs.

The API only pushes envelopes onto the main list; consumption, ack/nack,
dead-lettering, and crash recovery all live in the `analytics_worker`
service. See `services/analytics_worker/src/analytics/queue.py` for the
matching consumer.

Each envelope is `{"id": <uuid>, "payload": {...}, "attempts": <int>}`.
"""

from __future__ import annotations

import json
import uuid

from redis.asyncio import Redis

from src.core.config import config

redis_client: Redis = Redis.from_url(config.redis_url, decode_responses=True)


async def enqueue_job(payload: dict) -> None:
    envelope = {"id": uuid.uuid4().hex, "payload": payload, "attempts": 0}
    await redis_client.lpush(config.queue_name, json.dumps(envelope))


async def aclose() -> None:
    await redis_client.aclose()
