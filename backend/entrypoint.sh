#!/bin/bash
# Waits for Postgres to be ready before starting the application.
# This is a safety net in case the Docker Compose healthcheck timing is insufficient.

set -e

HOST="${POSTGRES_HOST:-postgres}"
PORT="${POSTGRES_PORT:-5432}"
MAX_RETRIES=30
RETRY_INTERVAL=3

echo "Waiting for Postgres at $HOST:$PORT..."

for i in $(seq 1 $MAX_RETRIES); do
  if pg_isready -h "$HOST" -p "$PORT" -q; then
    echo "Postgres is ready after $i attempt(s). Starting application..."
    exec "$@"
  fi
  echo "  Attempt $i/$MAX_RETRIES — not ready yet, retrying in ${RETRY_INTERVAL}s..."
  sleep "$RETRY_INTERVAL"
done

echo "ERROR: Postgres did not become ready after $((MAX_RETRIES * RETRY_INTERVAL))s. Exiting."
exit 1
