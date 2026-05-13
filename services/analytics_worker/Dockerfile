FROM python:3.12-slim-bookworm AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY services services

RUN uv sync --frozen --no-dev --package analytics_worker


FROM python:3.12-slim-bookworm AS runtime

# OpenCV (cv2) and ultralytics need OpenMP, libGL (manylinux cv2 links libGL.so.1),
# plus X11 client libs even for opencv-python-headless wheels (libxcb, libX11, etc.).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfontconfig1 \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Ultralytics calls os.access on ~/.config before mkdir; a missing .config is
# treated as non-writable and triggers a /tmp fallback + warning (see
# get_user_config_dir in ultralytics.utils).
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /home/app/.config \
    && chown -R app:app /home/app

WORKDIR /app
COPY --from=builder /app /app

# Pre-create the data directories used at runtime (uploads mount is shared
# with main_service, yolo is the model cache) so that Docker initializes
# the named volumes with the correct ownership when this container is the
# first to mount them.
RUN mkdir -p /data/uploads /data/yolo && chown -R app:app /data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/services/analytics_worker \
    UV_DEV_RELOAD=0

USER app

# Liveness is driven by the heartbeat file written each loop iteration
# (see src/analytics/worker.py); the HTTP probe used by analytics_api is
# not applicable here, so we skip HEALTHCHECK in the image and let the
# orchestrator (compose/K8s) own the probe definition.

# With UV_DEV_RELOAD=1, watchfiles restarts the worker when workspace Python changes.
# watchfiles 1.x: ``target [paths...]`` after options; ``--`` ends option parsing so the
# command string cannot be misparsed as a watch path (see watchfiles/cli.py resolve_path).
CMD ["sh", "-c", "if [ \"${UV_DEV_RELOAD}\" = \"1\" ] || [ \"${UV_DEV_RELOAD}\" = \"true\" ]; then exec watchfiles --target-type=command --filter=python -- \"python -m src.worker_main\" /app/packages /app/services/analytics_worker; else exec python -m src.worker_main; fi"]
