# Start FastAPI backend server directly (outside Docker), against the
# Postgres container's host-mapped port.
#
# backend/.env sets POSTGRES_HOST=postgres / POSTGRES_PORT=5432 for Docker
# Compose's internal network — that hostname doesn't resolve out here, so
# override it with the values Docker maps to localhost instead. load_dotenv()
# (called in database/db_connect.py) never overrides already-exported vars,
# so these take precedence over backend/.env.
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433

echo "Starting FastAPI backend server..."
cd "$(dirname "$0")"
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000