#!/bin/bash
# Pre-creates the tables langchain_postgres's PGVector store needs, and grants
# the read-only app user narrow write access to *only* those two tables.
#
# Why this exists: the backend connects as POSTGRES_READONLY_USER for
# everything, including RAG knowledge-base bootstrap and logging successful
# (question, SQL) pairs for future retrieval. Both need INSERT/UPDATE/DELETE
# on the vector-store tables, and initial setup needs CREATE TABLE. Granting
# any of that on the app's own data tables would defeat the point of the
# read-only user (see 02-readonly-user.sh). So instead we:
#   1. Create the vector-store tables here, as the admin user, once.
#   2. Grant DML (not CREATE/DROP/TRUNCATE) on just these two tables to the
#      read-only user.
# SQLAlchemy's create_all() (used internally by PGVector) skips CREATE TABLE
# for tables that already exist, so the backend's read-only connection never
# needs to run DDL at all.
#
# Schema mirrors langchain_postgres.vectorstores CollectionStore/EmbeddingStore
# as of langchain-postgres==0.0.17. If a future version changes that schema,
# update this file to match.

set -euo pipefail

if [[ -z "${POSTGRES_READONLY_USER:-}" ]]; then
  echo "WARNING: POSTGRES_READONLY_USER not set. Skipping vector-store table setup." >&2
  echo "         The backend will fail to start unless it connects as a user with CREATE." >&2
  exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
  CREATE TABLE IF NOT EXISTS langchain_pg_collection (
      uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR NOT NULL UNIQUE,
      cmetadata JSON
  );

  CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
      id VARCHAR PRIMARY KEY,
      collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,
      embedding VECTOR,
      document VARCHAR,
      cmetadata JSONB
  );

  CREATE INDEX IF NOT EXISTS ix_langchain_pg_embedding_collection_id
      ON langchain_pg_embedding (collection_id);

  GRANT SELECT, INSERT, UPDATE, DELETE
      ON langchain_pg_collection, langchain_pg_embedding
      TO "${POSTGRES_READONLY_USER}";
SQL

echo "Vector-store tables ready; scoped DML granted to '${POSTGRES_READONLY_USER}'."
