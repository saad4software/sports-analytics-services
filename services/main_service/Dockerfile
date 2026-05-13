FROM python:3.12-slim-bookworm AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY services services

RUN uv sync --frozen --no-dev --package main_service


FROM python:3.12-slim-bookworm AS runtime

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder /app /app

# Pre-create the uploads directory with ownership matching the runtime user.
# Docker copies these permissions onto a freshly initialized named volume,
# so the `app` user can write uploads at /data/uploads (compose default).
RUN mkdir -p /data/uploads && chown -R app:app /data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_DEV_RELOAD=0

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

# Set UV_DEV_RELOAD=1 and bind-mount packages + services (see docker-compose) for live reload.
CMD ["sh", "-c", "if [ \"${UV_DEV_RELOAD}\" = \"1\" ] || [ \"${UV_DEV_RELOAD}\" = \"true\" ]; then exec python -m uvicorn src.main:app --app-dir services/main_service --host 0.0.0.0 --port 8000 --reload; else exec python -m uvicorn src.main:app --app-dir services/main_service --host 0.0.0.0 --port 8000; fi"]
