# sports-analytics Helm chart

Deploys the five FastAPI services (`auth-service`, `media-service`,
`notifications-service`, `main-service`, `analytics-api`) plus the standalone
`analytics-worker` Deployment to any Kubernetes cluster. In-cluster Postgres
and Redis are bundled as minimal StatefulSets and can be disabled when pointing
at managed services.

## Architecture

```
                                +-> auth-service          (sports_auth)
                                |
Client -> Ingress -> main-service
                                |   +-> media-service     (sports_media)
                                +-->|
                                |   +-> notifications-service (sports_notifications)
                                |
                                +-> analytics-api -> Redis queue -> analytics-worker
                                                                       |
                                                                       +-> media-service
                                                                       +-> notifications-service
```

- Three pre-install/pre-upgrade `Job`s (`auth-migrate`, `media-migrate`,
  `notifications-migrate`) run `alembic upgrade head` against their owning
  databases. Each one reuses the service's image so the venv and Alembic
  config travel together.
- `analytics-worker` scales 0..N on the Redis queue length via a KEDA
  `ScaledObject` and uses a reliable BLMOVE-based queue so crashed pods do not
  drop jobs.
- `main-service` and `analytics-worker` share a ReadWriteMany `uploads` PVC.
  Storage classes that support RWX (NFS, EFS, Filestore, Azure Files) are
  required. Moving uploads to object storage is the documented follow-up.
- The bundled Postgres StatefulSet projects an init `ConfigMap` into
  `/docker-entrypoint-initdb.d/` so the per-service databases
  (`sports_auth`, `sports_media`, `sports_notifications`) are created on the
  first init of the data volume.

## Quick start

```bash
helm install sa deploy/helm/sports-analytics \
  --set image.tag=0.2.0 \
  --set authService.image.repository=ghcr.io/yourorg/auth-service \
  --set mediaService.image.repository=ghcr.io/yourorg/media-service \
  --set notificationsService.image.repository=ghcr.io/yourorg/notifications-service \
  --set mainService.image.repository=ghcr.io/yourorg/main-service \
  --set analyticsApi.image.repository=ghcr.io/yourorg/analytics-service \
  --set analyticsWorker.image.repository=ghcr.io/yourorg/analytics-worker \
  --set secrets.internalApiKey=$(openssl rand -hex 32) \
  --set secrets.jwtSecret=$(openssl rand -hex 32)
```

## Common toggles

| Value | Purpose |
|-------|---------|
| `postgres.enabled=false` + `secrets.{auth,media,notifications}DatabaseUrl=...` | Use Cloud SQL / RDS / AlloyDB |
| `redis.enabled=false` | Use managed Redis (override the `REDIS_URL` projected into the ConfigMap) |
| `analyticsWorker.keda.enabled=false` | Disable autoscaling, run fixed `analyticsWorker.replicas` |
| `ingress.tls.enabled=true` | Terminate TLS at the ingress |
| `networkPolicy.enabled=true` | Lock east-west traffic to the documented edges |
| `modelCache.url=https://.../yolo26x.pt` | Have the worker initContainer pull weights on first start |
| `secrets.existingSecret=my-secret` | Skip the chart-managed Secret and consume an external one |

The external Secret (when `secrets.existingSecret` is set) must expose:
`INTERNAL_API_KEY`, `JWT_SECRET`, `AUTH_DATABASE_URL`, `MEDIA_DATABASE_URL`,
`NOTIFICATIONS_DATABASE_URL`.

## Render manifests offline

```bash
helm template sa deploy/helm/sports-analytics > /tmp/sa.yaml
```

## Lint locally (matches CI)

```bash
helm lint deploy/helm/sports-analytics
helm template sa deploy/helm/sports-analytics | kubeconform -strict -summary
```

## Follow-ups (not implemented yet)

- Move uploads + model artifacts to object storage (MinIO/S3/GCS) so the
  RWX PVC goes away.
- Prometheus `/metrics` + OpenTelemetry tracing; Grafana dashboards.
- Model registry + signed artifact + versioned `YOLO_MODEL_PATH`.
- GPU scheduling (`nvidia.com/gpu`, CUDA base image) and batched inference.
- External secret store (SealedSecrets or ExternalSecrets Operator) wired in
  via a new `secrets.externalSecrets.*` block.
