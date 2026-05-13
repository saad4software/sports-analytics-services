"""Standalone entrypoint for the analytics worker.

Runs the worker loop in its own process (separate K8s Deployment /
Compose service) so heavy YOLO inference never blocks the API event
loop.
"""

import asyncio
import signal

from src.analytics import queue
from src.analytics.media_client import media_client
from src.analytics.notifications_client import notifications_client
from src.analytics.worker import worker_loop
from src.core.logging import setup_logging


async def main() -> None:
    setup_logging()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    try:
        await worker_loop(stop)
    finally:
        await media_client.aclose()
        await notifications_client.aclose()
        await queue.aclose()


if __name__ == "__main__":
    asyncio.run(main())
