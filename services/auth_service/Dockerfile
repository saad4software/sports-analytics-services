FROM python:3.12-slim-bookworm AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY services services

RUN uv sync --frozen --no-dev --package auth_service


FROM python:3.12-slim-bookworm AS runtime

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_DEV_RELOAD=0

USER app

EXPOSE 8002

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8002/health').status==200 else 1)"

CMD ["sh", "-c", "if [ \"${UV_DEV_RELOAD}\" = \"1\" ] || [ \"${UV_DEV_RELOAD}\" = \"true\" ]; then exec python -m uvicorn src.main:app --app-dir services/auth_service --host 0.0.0.0 --port 8002 --reload; else exec python -m uvicorn src.main:app --app-dir services/auth_service --host 0.0.0.0 --port 8002; fi"]
