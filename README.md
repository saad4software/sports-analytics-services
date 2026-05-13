# Sports Analytics Services

A small set of FastAPI microservices that process football videos and count
players per team plus referees per frame.

## Services

| Service | Port | Owns | Role |
|--------|------|------|------|
| `auth_service` | 8002 | `users` schema | Register / login by username; issues JWTs. Owns its own Postgres DB. |
| `media_service` | 8004 | `video_file` + `frame` schemas | Internal CRUD over videos and frames; `analytics_worker` PATCHes `video.status` over HTTP when jobs run. |
| `notifications_service` | 8005 | `notification` schema | Internal list + create routes; `analytics_worker` POSTs `processing_complete` / `processing_failed` rows. |
| `main_service` | 8000 | — | Public BFF: proxies auth, accepts multipart uploads, lists videos / notifications, streams files. |
| `analytics_service` | 8003 | — | Thin FastAPI enqueue endpoint that pushes video-processing jobs onto the Redis work queue. |
| `analytics_worker` | n/a | — | Standalone asyncio process that drains the Redis queue, runs the YOLO + HSV pipeline, writes frames and lifecycle updates to `media_service`, and creates notifications over HTTP. |

`packages/ml_core` holds the headless video processor and is consumed by
`analytics_worker`. `packages/db_core` is an `ml_core`-style shared
library (SQLModel session helpers, response middleware, exception
handlers, JWT helpers, internal-key guard) consumed by every Python
service that owns a database.

## Architecture

Each service that owns data has its own Postgres database and Alembic
project. Cross-service updates (video status, notifications) are driven
by `analytics_worker` calling internal HTTP routes on `media_service`
and `notifications_service` once a job is dequeued and running.

```
                                                          +-> media_service (sports_media)
                                                          |     ^   |   ^
Client --> main_service --> auth_service (sports_auth)    |     |   |   |  HTTP PATCH /internal/videos/{id}/status
   |                              ^                       |     |   |   |  HTTP POST /internal/frames/bulk
   |                              | HTTP (login/register)  |     |   |   |
   |                                                       |     |   |
   +-> /videos   --HTTP--> media_service ------------------+     |   |
   +-> /notifs   --HTTP--> notifications_service <---------------+   |
                            ^                                        |
                            | HTTP POST /internal/notifications      |
   +-> /analytics--HTTP--> analytics_api -- LPUSH --> Redis queue    |
                                                       +--BLMOVE -----+
                                                       |
                                                       +-> analytics_worker
```

Key properties:

- **Separate databases.** `auth_service`, `media_service`, and
  `notifications_service` each use their own logical database
  (`sports_auth`, `sports_media`, `sports_notifications`). Foreign keys
  never cross service boundaries — cross-service references (e.g.
  `notification.user_id`, `video.user_id`) are plain integers with no
  DB-enforced constraint.
- **Migrations per service.** Each owning service ships an Alembic
  project (`services/<name>/migrations/`) that is run on startup via an
  `*_migrate` Compose job, mirroring the pre-install / pre-upgrade Helm
  `Job` pattern.
- **Worker-owned lifecycle updates.** After `analytics_worker` pulls a
  job from the queue it PATCHes `video.status` to `processing`, streams
  frames over HTTP, then PATCHes `done` or `failed` (with
  `error_message`) and POSTs matching notifications. Upload responses
  from `main_service` may still show `uploaded` until the worker starts.
- **Frames are HTTP.** Frames are a high-volume write (50 rows per
  batch, many batches per video). The worker writes them directly to
  `media_service`’s internal `/internal/frames/bulk` endpoint.

The Redis queue used by `analytics_service → analytics_worker` is
unchanged: reliable BLMOVE-based queue with per-pod processing lists and
an attempts-counted dead-letter list.

## Setup

Requires Python 3.12+, [`uv`](https://docs.astral.sh/uv/), a running
**PostgreSQL 16+** instance, and a Redis server.

```bash
cp .env.example .env
# edit .env: set INTERNAL_API_KEY, JWT_SECRET, REDIS_URL, and
# AUTH_DATABASE_URL / MEDIA_DATABASE_URL / NOTIFICATIONS_DATABASE_URL.
```

Create one database per owning service (matching the URLs above), for
example:

```bash
createdb sports_auth
createdb sports_media
createdb sports_notifications
```

```bash
uv sync --all-packages
```

### Run with Docker

Create **`compose.env`** from the example. This file holds **secrets and
Compose-time settings**:

```bash
cp compose.env.example compose.env
docker compose up --build
```

The Compose stack:

- Boots a single Postgres 16 instance and uses
  `deploy/postgres/init-databases.sh` (mounted at
  `/docker-entrypoint-initdb.d/`) to `CREATE DATABASE sports_auth`,
  `sports_media`, and `sports_notifications` on first init.
- Runs `auth_migrate`, `media_migrate`, and `notifications_migrate` as
  one-shot Alembic jobs against their respective databases.
- Starts `auth_service` (8002), `media_service` (8004),
  `notifications_service` (8005), `analytics_api` (8003),
  `analytics_worker`, and `main_service` (8000).
- Persists uploads in the `main_uploads` volume (`UPLOAD_DIR=/data/uploads`)
  and YOLO weights in `yolo_weights`.

Stop and remove containers (volumes are kept unless you add `-v`):

```bash
docker compose down
```

### Database migrations

Each owning service runs its own Alembic project. To create / apply
migrations locally:

```bash
# Auth (users)
cd services/auth_service
export AUTH_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sports_auth
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"  # after model changes

# Media (videos + frames)
cd services/media_service
export MEDIA_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sports_media
uv run alembic upgrade head

# Notifications
cd services/notifications_service
export NOTIFICATIONS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sports_notifications
uv run alembic upgrade head
```

Each project ships its own initial revision; you only need
`revision --autogenerate` when that service’s SQLModel schema changes.

### Run all services (local, without Docker)

```bash
# Auth (owns users)
uv run --package auth_service uvicorn src.main:app \
  --app-dir services/auth_service --reload --port 8002

# Media (owns videos + frames)
uv run --package media_service uvicorn src.main:app \
  --app-dir services/media_service --reload --port 8004

# Notifications (owns notifications)
uv run --package notifications_service uvicorn src.main:app \
  --app-dir services/notifications_service --reload --port 8005

# Main (BFF)
uv run --package main_service uvicorn src.main:app \
  --app-dir services/main_service --reload --port 8000

# Analytics API (HTTP enqueue)
uv run --package analytics_service uvicorn src.main:app \
  --app-dir services/analytics_service --reload --port 8003

# Analytics worker (YOLO + HTTP side effects to media / notifications)
uv run --package analytics_worker --directory services/analytics_worker \
  python -m src.worker_main
```

## API surface (Main, public)

| Method | Path | Purpose |
|-------|------|---------|
| `POST` | `/auth/register` | Proxy to Auth: `{username, password}` |
| `POST` | `/auth/login` | Proxy to Auth: returns `{access_token}` |
| `POST` | `/videos` (multipart) | Fields: `file`, `first_team_color`, `second_team_color` (each one of `red\|white\|black`, must differ). |
| `GET`  | `/videos` | List the caller's videos with status and links. |
| `GET`  | `/videos/{id}` | Video metadata + processed frame list. |
| `GET`  | `/videos/{id}/media` | Stream / download the original file. |
| `GET`  | `/notifications` | List notifications for the current user. |

## Data model

- **User** (`auth_service` / `sports_auth.user`): `id`, `username`,
  `hashed_password`.
- **VideoFile** (`media_service` / `sports_media.video_file`): per-user
  upload (`user_id` is unconstrained — users live in another service);
  `first_team_color`, `second_team_color`, `status` (`uploaded` /
  `processing` / `done` / `failed`), `stored_path`.
- **Frame** (`media_service` / `sports_media.frame`): `frame_number`,
  `time`, `first_team_count`, `second_team_count`, `referee_count`.
- **Notification** (`notifications_service` /
  `sports_notifications.notification`): `processing_complete` /
  `processing_failed` rows written by `analytics_worker` over HTTP.

## Cross-service calls from `analytics_worker`

After a job is dequeued, the worker calls `media_service` internal routes
to update `video_file.status` and bulk-insert frames, and
`notifications_service` `POST /internal/notifications` when a run
finishes or fails. Redis is used only for the analytics job queue (not
for pub/sub between services).

## Deploy on Kubernetes

The Helm chart at
[`deploy/helm/sports-analytics/`](deploy/helm/sports-analytics/) mirrors
`docker-compose.yml`:

- One `Deployment` per service (`auth-service`, `media-service`,
  `notifications-service`, `main-service`, `analytics-api`,
  `analytics-worker`).
- Three pre-install / pre-upgrade `Job`s (`auth-migrate`,
  `media-migrate`, `notifications-migrate`) running
  `alembic upgrade head` against their respective databases, each one
  reusing the service's own image.
- Optional in-cluster Postgres + Redis StatefulSets. The bundled Postgres
  projects `deploy/postgres/init-databases.sh` (rendered into a
  ConfigMap) to `/docker-entrypoint-initdb.d/` so `sports_auth`,
  `sports_media`, and `sports_notifications` are created on first init.
- A `PersistentVolumeClaim` for uploads (RWX) shared between
  `main-service` (rw) and `analytics-worker` (ro).
- `HorizontalPodAutoscaler`s on the API tiers and a KEDA `ScaledObject`
  on `analytics-worker` driven by the Redis queue length.
- ServiceAccounts per Deployment and opt-in NetworkPolicies.

Render or install with:

```bash
helm lint deploy/helm/sports-analytics
helm template sa deploy/helm/sports-analytics > /tmp/sa.yaml
helm install sa deploy/helm/sports-analytics \
  --set secrets.internalApiKey=$(openssl rand -hex 32) \
  --set secrets.jwtSecret=$(openssl rand -hex 32)
```

See [`deploy/helm/sports-analytics/README.md`](deploy/helm/sports-analytics/README.md)
for the full list of toggles (managed Postgres / Redis, TLS, KEDA,
NetworkPolicies, model cache prefetch, externally-managed Secret).

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request:

- **Lint** — `uv run ruff check .` against the conservative day-1 rule
  set configured in the root `pyproject.toml`.
- **Test** — `pytest` per service (matrixed) because the workspace
  ships overlapping `src.*` packages that collide at the repo root.
- **Helm** — `helm lint`, `helm template` for the default and external-
  Postgres profiles, then `kubeconform -strict` against rendered
  manifests.
- **Build** — smoke `docker build` per service Dockerfile (no push) so
  Dockerfile regressions are caught early. Gated on `lint` + `test`.

## Security notes

- `INTERNAL_API_KEY` guards every internal route on `media_service` and
  `notifications_service` (including notification create). Never expose those routes publicly.
- `JWT_SECRET` is shared by Auth (signs) and Main / Analytics (verify).
  Keep the same value on all three.
- Do not commit production Redis credentials. Set `REDIS_URL` via `.env`
  only.
- Do not commit **`compose.env`**. Use the tracked
  **`compose.env.example`** as the template.
