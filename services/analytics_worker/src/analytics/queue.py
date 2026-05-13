"""Reliable Redis queue consumer for analytics jobs.

Pattern (per-pod processing list):
- dequeue:        BLMOVE queue RIGHT -> processing:<consumer> LEFT  (atomic)
- ack on success: LREM   processing:<consumer> 0 envelope
- nack on fail:   increment attempts on the envelope, then
                  - if attempts < max: LREM + LPUSH back onto queue head
                  - else:              LREM + LPUSH onto dead-letter list
- crash recovery on startup: any envelope still in processing:<consumer>
                  is moved back to the head of the main queue.

Each envelope is `{"id": <uuid>, "payload": {...}, "attempts": <int>}`.
This gives at-least-once semantics: a worker that crashes mid-job will
re-process the same job after recovery.

The producer side (LPUSH onto the main queue) lives in the
analytics_service API; the worker only consumes.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Optional

from redis.asyncio import Redis

from src.core.config import config

logger = logging.getLogger(__name__)

CONSUMER_ID = os.getenv("WORKER_CONSUMER_ID") or os.getenv("HOSTNAME") or f"local-{uuid.uuid4().hex[:8]}"
MAX_ATTEMPTS = int(os.getenv("ANALYTICS_MAX_ATTEMPTS", "3"))


def _processing_key() -> str:
    return f"{config.queue_name}:processing:{CONSUMER_ID}"


def _dead_key() -> str:
    return f"{config.queue_name}:dead"


redis_client: Redis = Redis.from_url(config.redis_url, decode_responses=True)


@dataclass
class AckableJob:
    """Wraps a dequeued job so callers can explicitly ack/nack it."""

    raw: str
    envelope: dict

    @property
    def payload(self) -> dict:
        return self.envelope["payload"]

    async def ack(self) -> None:
        await redis_client.lrem(_processing_key(), 1, self.raw)

    async def nack(self) -> None:
        envelope = dict(self.envelope)
        envelope["attempts"] = int(envelope.get("attempts", 0)) + 1
        pipe = redis_client.pipeline()
        pipe.lrem(_processing_key(), 1, self.raw)
        if envelope["attempts"] >= MAX_ATTEMPTS:
            logger.error(
                "Job %s exceeded max attempts (%d); moving to dead-letter list",
                envelope.get("id"),
                MAX_ATTEMPTS,
            )
            pipe.lpush(_dead_key(), json.dumps(envelope))
        else:
            pipe.lpush(config.queue_name, json.dumps(envelope))
        await pipe.execute()


async def dequeue_job(timeout: int = 5) -> Optional[AckableJob]:
    """Atomically move one job from the main queue to this consumer's
    processing list. Returns None on timeout.
    """
    raw = await redis_client.blmove(
        config.queue_name,
        _processing_key(),
        timeout=timeout,
        src="RIGHT",
        dest="LEFT",
    )
    if raw is None:
        return None
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed entry: drop from the processing list so it doesn't loop.
        logger.exception("Malformed queue entry; discarding: %r", raw)
        await redis_client.lrem(_processing_key(), 1, raw)
        return None
    if not isinstance(envelope, dict) or "payload" not in envelope:
        envelope = {"id": uuid.uuid4().hex, "payload": envelope, "attempts": 0}
    return AckableJob(raw=raw, envelope=envelope)


async def recover_in_flight() -> int:
    """Move any leftover entries in this consumer's processing list back to
    the head of the main queue. Called at worker startup to recover from
    crashes."""
    key = _processing_key()
    moved = 0
    while True:
        raw = await redis_client.rpoplpush(key, config.queue_name)
        if raw is None:
            break
        moved += 1
    if moved:
        logger.warning("Recovered %d in-flight job(s) from %s", moved, key)
    return moved


async def aclose() -> None:
    await redis_client.aclose()
