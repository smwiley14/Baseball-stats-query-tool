#!/bin/bash
# Refreshes the materialized views created by db/05-materialize-views.sh.
#
# Run this whenever you load new data (see db/load_data.sh) — materialized
# views don't update automatically, so without this, new games/seasons won't
# show up in season leaderboards or career totals until refreshed.
#
# Usage: run directly from the host, same as db/load_data.sh — connects to
# Postgres via its host-mapped port (127.0.0.1:5433 by default in
# docker-compose.yaml).
#   ./db/refresh_materialized_views.sh

set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-retrosheet}"
DB_USER="${DB_USER:-baseball}"
DB_PASSWORD="${DB_PASSWORD:-baseball}"

export PGPASSWORD="$DB_PASSWORD"

echo "Refreshing materialized views..."

for view in all_batting_seasons all_pitching_seasons qualified_batting_seasons qualified_pitching_seasons v_player_career_batting v_player_career_pitching; do
  echo "  Refreshing $view..."
  psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -c "REFRESH MATERIALIZED VIEW CONCURRENTLY $view;"
done

unset PGPASSWORD
echo "Done."
