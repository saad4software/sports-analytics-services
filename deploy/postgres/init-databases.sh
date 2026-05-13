#!/usr/bin/env bash
# Bootstrap one database per owning service.
#
# This file is mounted into the official `postgres:16` image at
# /docker-entrypoint-initdb.d/, which runs *.sh files on the very first
# init of the data directory. After that the volume is reused as-is; if
# you change this list, drop `postgres_data` to re-initialise.
set -euo pipefail

create_db() {
  local db="$1"
  echo "Ensuring database '$db' exists"
  psql -v ON_ERROR_STOP=1 \
       --username "${POSTGRES_USER}" \
       --dbname postgres \
       -tc "SELECT 1 FROM pg_database WHERE datname = '${db}'" | grep -q 1 \
    || psql -v ON_ERROR_STOP=1 \
            --username "${POSTGRES_USER}" \
            --dbname postgres \
            -c "CREATE DATABASE \"${db}\""
}

# Database names; URLs in compose.env must use the same names.
create_db "sports_auth"
create_db "sports_media"
create_db "sports_notifications"
