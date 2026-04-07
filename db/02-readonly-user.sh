#!/bin/bash
# Creates a read-only application user on first Postgres container init.
# Runs automatically via docker-entrypoint-initdb.d (only on first boot).
#
# The application backend connects as this user. Even if it is fully
# compromised it physically cannot INSERT, UPDATE, DELETE, or DROP anything.
#
# Required env vars (set in .env):
#   POSTGRES_READONLY_USER     — username for the read-only account
#   POSTGRES_READONLY_PASSWORD — password for the read-only account

set -euo pipefail

if [[ -z "${POSTGRES_READONLY_USER:-}" || -z "${POSTGRES_READONLY_PASSWORD:-}" ]]; then
  echo "WARNING: POSTGRES_READONLY_USER or POSTGRES_READONLY_PASSWORD not set." >&2
  echo "         Skipping read-only user creation." >&2
  exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
  -- Create the user only if it doesn't already exist
  DO \$\$
  BEGIN
    IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_READONLY_USER}'
    ) THEN
      CREATE USER "${POSTGRES_READONLY_USER}" WITH PASSWORD '${POSTGRES_READONLY_PASSWORD}';
      RAISE NOTICE 'Created read-only user: ${POSTGRES_READONLY_USER}';
    ELSE
      RAISE NOTICE 'Read-only user already exists: ${POSTGRES_READONLY_USER}';
    END IF;
  END
  \$\$;

  -- Connect permission
  GRANT CONNECT ON DATABASE "${POSTGRES_DB}" TO "${POSTGRES_READONLY_USER}";

  -- Schema usage
  GRANT USAGE ON SCHEMA public TO "${POSTGRES_READONLY_USER}";

  -- SELECT on all existing tables
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO "${POSTGRES_READONLY_USER}";

  -- SELECT on all future tables automatically
  ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO "${POSTGRES_READONLY_USER}";
SQL

echo "Read-only user '${POSTGRES_READONLY_USER}' configured successfully."
