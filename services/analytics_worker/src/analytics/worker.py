"""Analytics worker job processor.

1. Pull a job off the Redis work queue.
2. Fetch the video row from media_service.
3. PATCH ``video_file.status`` to ``processing`` (job actually started).
4. Stream YOLO frames in batches into media_service.
5. PATCH status to ``done`` or ``failed`` and POST notifications over HTTP.
"""

import asyncio
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any

from ml_core import VideoProcessor

from src.analytics.media_client import media_client
from src.analytics.notifications_client import notifications_client
from src.analytics.queue import (
    AckableJob,
    dequeue_job,
    recover_in_flight,
)
from src.core.config import config

logger = logging.getLogger(__name__)

# One processor (and one YOLO model) per worker process; loaded lazily.
_processor = VideoProcessor(model_path=config.yolo_model_path)

BATCH_SIZE = 50
_FRAME_STREAM_DONE: Any = object()
_FRAME_STREAM_BUFFER = 200
HEARTBEAT_PATH = os.getenv("WORKER_HEARTBEAT_PATH", "/tmp/heartbeat")


def _touch_heartbeat() -> None:
    """Update the heartbeat file used by the K8s exec liveness probe."""
    try:
        with open(HEARTBEAT_PATH, "w") as f:
            f.write(str(time.time()))
    except OSError:
        logger.debug("Could not write heartbeat file", exc_info=True)


async def _stream_frames(video, video_id: int) -> int:
    """Stream frames from the sync ml_core iterator into batched media writes.

    The YOLO loop runs in a worker thread; each FrameResult is pushed
    into a bounded asyncio.Queue. The async side drains the queue,
    buffers up to BATCH_SIZE frames, and flushes via the media client.
    Memory stays flat regardless of how long the video is.
    """
    loop = asyncio.get_running_loop()
    handoff: asyncio.Queue = asyncio.Queue(maxsize=_FRAME_STREAM_BUFFER)
    started_at = datetime.now(timezone.utc)

    def produce() -> None:
        try:
            for fr in _processor.iter_frames(
                video["stored_path"],
                first_team_color=video["first_team_color"],
                second_team_color=video["second_team_color"],
                started_at=started_at,
            ):
                asyncio.run_coroutine_threadsafe(handoff.put(fr), loop).result()
        except BaseException as exc:
            asyncio.run_coroutine_threadsafe(handoff.put(exc), loop).result()
        finally:
            asyncio.run_coroutine_threadsafe(
                handoff.put(_FRAME_STREAM_DONE), loop
            ).result()

    producer = threading.Thread(target=produce, name=f"yolo-{video_id}", daemon=True)
    producer.start()

    batch: list[dict] = []
    total = 0
    pending_error: BaseException | None = None
    try:
        while True:
            item = await handoff.get()
            if item is _FRAME_STREAM_DONE:
                break
            if isinstance(item, BaseException):
                pending_error = item
                break
            batch.append(
                {
                    "frame_number": item.frame_number,
                    "time": item.time.isoformat(),
                    "first_team_count": item.first_team_count,
                    "second_team_count": item.second_team_count,
                    "referee_count": item.referee_count,
                }
            )
            total += 1
            if len(batch) >= BATCH_SIZE:
                await media_client.bulk_create_frames(video_id, batch)
                batch.clear()
        if batch:
            await media_client.bulk_create_frames(video_id, batch)
    finally:
        await asyncio.to_thread(producer.join)

    if pending_error is not None:
        raise pending_error
    return total


async def _process_video(job: dict) -> None:
    video_id = job["video_id"]
    logger.info("Processing video %s", video_id)

    video = await media_client.get_video(video_id)
    user_id = video["user_id"]
    original_filename = video["original_filename"]

    await media_client.update_video_status(
        video_id, status="processing", ignore_missing=False
    )

    try:
        total = await _stream_frames(video, video_id)
    except Exception as exc:
        logger.exception("Failed to process video %s", video_id)
        err = str(exc)[:2000]
        await media_client.update_video_status(
            video_id,
            status="failed",
            error_message=err,
            ignore_missing=True,
        )
        try:
            await notifications_client.create_notification(
                user_id=user_id,
                video_id=video_id,
                notification_type="processing_failed",
                message=(
                    f"Video '{original_filename}' failed: {err}"
                )[:1024],
            )
        except Exception:
            logger.exception(
                "Could not persist processing_failed notification for video %s",
                video_id,
            )
        return

    await media_client.update_video_status(
        video_id, status="done", error_message=None, ignore_missing=True
    )
    try:
        await notifications_client.create_notification(
            user_id=user_id,
            video_id=video_id,
            notification_type="processing_complete",
            message=(
                f"Video '{original_filename}' has finished processing."
            )[:1024],
        )
    except Exception:
        logger.exception(
            "Could not persist processing_complete notification for video %s",
            video_id,
        )
    logger.info("Finished video %s (%d frames)", video_id, total)


async def worker_loop(stop_event: asyncio.Event) -> None:
    logger.info("Analytics worker loop started")
    try:
        await recover_in_flight()
    except Exception:
        logger.exception("Failed to recover in-flight jobs on startup")

    while not stop_event.is_set():
        _touch_heartbeat()
        try:
            ackable: AckableJob | None = await dequeue_job(timeout=2)
        except Exception:
            logger.exception("Failed to read from queue; retrying in 1s")
            await asyncio.sleep(1)
            continue
        if ackable is None:
            continue
        try:
            await _process_video(ackable.payload)
            await ackable.ack()
        except Exception:
            logger.exception("Unhandled error in worker job")
            try:
                await ackable.nack()
            except Exception:
                logger.exception("Failed to nack job; leaving in processing list")
    logger.info("Analytics worker loop stopped")
