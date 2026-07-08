#!/bin/bash
# Converts the season/career aggregate views into materialized views.
#
# Why: these views re-aggregate the entire batting_stats/pitching_stats
# tables from scratch on every query (a CTE-heavy GROUP BY over the full
# history). For career-total questions with no team/season filter this
# measured 175s in production. Materializing pre-computes the result once;
# queries against it are then a simple index lookup.
#
# Tradeoff: materialized views go stale after new data loads. Re-run
# db/refresh_materialized_views.sh whenever you load new data (see
# db/load_data.sh). This script only needs to run once per database.
#
# Runs automatically via docker-entrypoint-initdb.d on a fresh database.
# For an existing database, run manually:
#   docker compose exec -T postgres bash /docker-entrypoint-initdb.d/05-materialize-views.sh

set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-'SQL'
  -- DROP VIEW/DROP MATERIALIZED VIEW both error (not just no-op) if the
  -- object exists as the *other* kind, so IF EXISTS alone can't make this
  -- idempotent across "was a plain view" vs "already materialized" (on a
  -- re-run). Check pg_class.relkind and issue the right DROP dynamically.
  CREATE OR REPLACE FUNCTION pg_temp.drop_view_or_matview(name text) RETURNS void AS $f$
  DECLARE
    kind "char";
  BEGIN
    SELECT relkind INTO kind FROM pg_class WHERE relname = name AND relnamespace = 'public'::regnamespace;
    IF kind = 'm' THEN
      EXECUTE format('DROP MATERIALIZED VIEW %I CASCADE', name);
    ELSIF kind = 'v' THEN
      EXECUTE format('DROP VIEW %I CASCADE', name);
    END IF;
  END;
  $f$ LANGUAGE plpgsql;

  SELECT pg_temp.drop_view_or_matview('all_batting_seasons');
  CREATE MATERIALIZED VIEW all_batting_seasons AS
      WITH team_games AS (
          SELECT
              season,
              team,
              COUNT(*) AS games
          FROM (
              SELECT season, home_team_id AS team
              FROM games
              WHERE LOWER(game_type) = 'regular'

              UNION ALL

              SELECT season, away_team_id AS team
              FROM games
              WHERE LOWER(game_type) = 'regular'
          ) g
          GROUP BY season, team
      ),

      season_team_games AS (
          SELECT
              season,
              MAX(games) AS team_games
          FROM team_games
          GROUP BY season
      ),

      player_season_stats AS (
          SELECT
              bs.player_id,
              bs.team_id,
              bs.season,
              MIN(g.game_date) AS game_date,

              SUM(bs.plate_appearances) AS plate_appearances,
              SUM(bs.at_bats) AS at_bats,
              SUM(bs.hits) AS hits,
              SUM(bs.singles) AS singles,
              SUM(bs.doubles) AS doubles,
              SUM(bs.triples) AS triples,
              SUM(bs.home_runs) AS home_runs,
              SUM(bs.runs) AS runs,
              SUM(bs.rbis) AS rbis,
              SUM(bs.walks) AS walks,
              SUM(bs.intentional_walks) AS intentional_walks,
              SUM(bs.strikeouts) AS strikeouts,
              SUM(bs.hit_by_pitch) AS hit_by_pitch,
              SUM(bs.sacrifice_hits) AS sacrifice_hits,
              SUM(bs.sacrifice_flies) AS sacrifice_flies,
              SUM(bs.stolen_bases) AS stolen_bases,
              SUM(bs.caught_stealing) AS caught_stealing,
              SUM(bs.grounded_into_double_play) AS grounded_into_double_play,
              SUM(bs.reached_on_error) AS reached_on_error

          FROM batting_stats bs
          JOIN games g
              ON bs.game_id = g.game_id
          JOIN teams th
              ON g.home_team_id = th.team_id
          JOIN teams ta
              ON g.away_team_id = ta.team_id

          WHERE LOWER(g.game_type) = 'regular'
          AND th.league IN ('AL','NL')
          AND ta.league IN ('AL','NL')

          GROUP BY
              bs.player_id,
              bs.team_id,
              bs.season
      )

      SELECT
          ps.*,

          ROUND(
              ps.hits::DECIMAL / NULLIF(ps.at_bats,0),
              3
          ) AS batting_average,

          ROUND(
              (ps.hits + ps.walks + ps.hit_by_pitch)::DECIMAL /
              NULLIF(ps.at_bats + ps.walks + ps.hit_by_pitch + ps.sacrifice_flies,0),
              3
          ) AS on_base_percentage,

          ROUND(
              (ps.singles + 2*ps.doubles + 3*ps.triples + 4*ps.home_runs)::DECIMAL /
              NULLIF(ps.at_bats,0),
              3
          ) AS slugging_percentage,

          ROUND(
              (
                  (ps.hits + ps.walks + ps.hit_by_pitch)::DECIMAL /
                  NULLIF(ps.at_bats + ps.walks + ps.hit_by_pitch + ps.sacrifice_flies,0)
              )
              +
              (
                  (ps.singles + 2*ps.doubles + 3*ps.triples + 4*ps.home_runs)::DECIMAL /
                  NULLIF(ps.at_bats,0)
              ),
              3
          ) AS ops

      FROM player_season_stats ps
      JOIN season_team_games sg
          ON ps.season = sg.season;
  CREATE UNIQUE INDEX ON all_batting_seasons (player_id, team_id, season);


  SELECT pg_temp.drop_view_or_matview('all_pitching_seasons');
  CREATE MATERIALIZED VIEW all_pitching_seasons AS
      WITH season_games AS (
          SELECT
              season,
              COUNT(DISTINCT game_id) / COUNT(DISTINCT home_team_id) AS team_games
          FROM games
          WHERE LOWER(game_type) = 'regular'
          GROUP BY season
      )

      SELECT
          ps.player_id,
          ps.team_id,
          ps.season,

          MIN(ps.game_date) AS first_game,
          MAX(ps.game_date) AS last_game,

          SUM(ps.outs_pitched) AS outs_pitched,
          ROUND(SUM(ps.outs_pitched) / 3.0, 1) AS innings_pitched,

          SUM(ps.batters_faced) AS batters_faced,
          SUM(ps.hits_allowed) AS hits_allowed,
          SUM(ps.doubles_allowed) AS doubles_allowed,
          SUM(ps.triples_allowed) AS triples_allowed,
          SUM(ps.home_runs_allowed) AS home_runs_allowed,
          SUM(ps.runs_allowed) AS runs_allowed,
          SUM(ps.earned_runs) AS earned_runs,
          SUM(ps.walks_allowed) AS walks_allowed,
          SUM(ps.intentional_walks) AS intentional_walks,
          SUM(ps.strikeouts) AS strikeouts,
          SUM(ps.hit_batters) AS hit_batters,

          SUM(ps.wild_pitches) AS wild_pitches,
          SUM(ps.balks) AS balks,

          SUM(ps.sacrifice_hits_allowed) AS sacrifice_hits_allowed,
          SUM(ps.sacrifice_flies_allowed) AS sacrifice_flies_allowed,

          SUM(ps.stolen_bases_allowed) AS stolen_bases_allowed,
          SUM(ps.caught_stealing) AS caught_stealing,

          SUM(ps.passed_balls) AS passed_balls,

          SUM(CASE WHEN ps.win THEN 1 ELSE 0 END) AS wins,
          SUM(CASE WHEN ps.loss THEN 1 ELSE 0 END) AS losses,
          SUM(CASE WHEN ps.save THEN 1 ELSE 0 END) AS saves,

          SUM(CASE WHEN ps.game_started THEN 1 ELSE 0 END) AS games_started,
          SUM(CASE WHEN ps.complete_game THEN 1 ELSE 0 END) AS complete_games,

          ROUND(
              (SUM(ps.earned_runs) * 9.0) /
              NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
              2
          ) AS era,

          ROUND(
              (SUM(ps.walks_allowed) + SUM(ps.hits_allowed))::decimal /
              NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
              3
          ) AS whip,

          ROUND(
              SUM(ps.hits_allowed)::decimal /
              NULLIF(
                  SUM(ps.batters_faced)
                  - SUM(ps.walks_allowed)
                  - SUM(ps.hit_batters)
                  - SUM(ps.sacrifice_hits_allowed)
                  - SUM(ps.sacrifice_flies_allowed),
              0),
              3
          ) AS opponent_batting_avg,

          ROUND(
              (SUM(ps.strikeouts) * 9.0) /
              NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
              2
          ) AS k_per_9,

          ROUND(
              (SUM(ps.walks_allowed) * 9.0) /
              NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
              2
          ) AS bb_per_9

      FROM pitching_stats ps
      JOIN games g ON ps.game_id = g.game_id
      JOIN teams t ON g.home_team_id = t.team_id
      JOIN season_games sg ON sg.season = ps.season

      WHERE
          LOWER(g.game_type) = 'regular'
          AND t.league IN ('AL', 'NL')

      GROUP BY
          ps.player_id,
          ps.team_id,
          ps.season,
          sg.team_games;
  CREATE UNIQUE INDEX ON all_pitching_seasons (player_id, team_id, season);


  SELECT pg_temp.drop_view_or_matview('qualified_batting_seasons');
  CREATE MATERIALIZED VIEW qualified_batting_seasons AS
      WITH team_games AS (
          SELECT
              season,
              team,
              COUNT(*) AS games
          FROM (
              SELECT season, home_team_id AS team
              FROM games
              WHERE LOWER(game_type) = 'regular'

              UNION ALL

              SELECT season, away_team_id AS team
              FROM games
              WHERE LOWER(game_type) = 'regular'
          ) g
          GROUP BY season, team
      ),

      season_team_games AS (
          SELECT
              season,
              MAX(games) AS team_games
          FROM team_games
          GROUP BY season
      ),

      player_season_stats AS (
          SELECT
              bs.player_id,
              bs.team_id,
              bs.season,
              MIN(g.game_date) AS game_date,

              SUM(bs.plate_appearances) AS plate_appearances,
              SUM(bs.at_bats) AS at_bats,
              SUM(bs.hits) AS hits,
              SUM(bs.singles) AS singles,
              SUM(bs.doubles) AS doubles,
              SUM(bs.triples) AS triples,
              SUM(bs.home_runs) AS home_runs,
              SUM(bs.runs) AS runs,
              SUM(bs.rbis) AS rbis,
              SUM(bs.walks) AS walks,
              SUM(bs.intentional_walks) AS intentional_walks,
              SUM(bs.strikeouts) AS strikeouts,
              SUM(bs.hit_by_pitch) AS hit_by_pitch,
              SUM(bs.sacrifice_hits) AS sacrifice_hits,
              SUM(bs.sacrifice_flies) AS sacrifice_flies,
              SUM(bs.stolen_bases) AS stolen_bases,
              SUM(bs.caught_stealing) AS caught_stealing,
              SUM(bs.grounded_into_double_play) AS grounded_into_double_play,
              SUM(bs.reached_on_error) AS reached_on_error

          FROM batting_stats bs
          JOIN games g
              ON bs.game_id = g.game_id
          JOIN teams th
              ON g.home_team_id = th.team_id
          JOIN teams ta
              ON g.away_team_id = ta.team_id

          WHERE LOWER(g.game_type) = 'regular'
          AND th.league IN ('AL','NL')
          AND ta.league IN ('AL','NL')

          GROUP BY
              bs.player_id,
              bs.team_id,
              bs.season
      )

      SELECT
          ps.*,

          ROUND(
              ps.hits::DECIMAL / NULLIF(ps.at_bats,0),
              3
          ) AS batting_average,

          ROUND(
              (ps.hits + ps.walks + ps.hit_by_pitch)::DECIMAL /
              NULLIF(ps.at_bats + ps.walks + ps.hit_by_pitch + ps.sacrifice_flies,0),
              3
          ) AS on_base_percentage,

          ROUND(
              (ps.singles + 2*ps.doubles + 3*ps.triples + 4*ps.home_runs)::DECIMAL /
              NULLIF(ps.at_bats,0),
              3
          ) AS slugging_percentage,

          ROUND(
              (
                  (ps.hits + ps.walks + ps.hit_by_pitch)::DECIMAL /
                  NULLIF(ps.at_bats + ps.walks + ps.hit_by_pitch + ps.sacrifice_flies,0)
              )
              +
              (
                  (ps.singles + 2*ps.doubles + 3*ps.triples + 4*ps.home_runs)::DECIMAL /
                  NULLIF(ps.at_bats,0)
              ),
              3
          ) AS ops

      FROM player_season_stats ps
      JOIN season_team_games sg
          ON ps.season = sg.season
      WHERE
          ps.plate_appearances >= ROUND(3.1 * sg.team_games);
  CREATE UNIQUE INDEX ON qualified_batting_seasons (player_id, team_id, season);


  SELECT pg_temp.drop_view_or_matview('qualified_pitching_seasons');
  CREATE MATERIALIZED VIEW qualified_pitching_seasons AS
      WITH season_games AS (
          SELECT
              season,
              COUNT(DISTINCT game_id) / COUNT(DISTINCT home_team_id) AS team_games
          FROM games
          WHERE LOWER(game_type) = 'regular'
          GROUP BY season
      )

      SELECT
          ps.player_id,
          ps.team_id,
          ps.season,

          MIN(ps.game_date) AS first_game,
          MAX(ps.game_date) AS last_game,

          SUM(ps.outs_pitched) AS outs_pitched,
          ROUND(SUM(ps.outs_pitched) / 3.0, 1) AS innings_pitched,

          SUM(ps.batters_faced) AS batters_faced,
          SUM(ps.hits_allowed) AS hits_allowed,
          SUM(ps.doubles_allowed) AS doubles_allowed,
          SUM(ps.triples_allowed) AS triples_allowed,
          SUM(ps.home_runs_allowed) AS home_runs_allowed,
          SUM(ps.runs_allowed) AS runs_allowed,
          SUM(ps.earned_runs) AS earned_runs,
          SUM(ps.walks_allowed) AS walks_allowed,
          SUM(ps.intentional_walks) AS intentional_walks,
          SUM(ps.strikeouts) AS strikeouts,
          SUM(ps.hit_batters) AS hit_batters,

          SUM(ps.wild_pitches) AS wild_pitches,
          SUM(ps.balks) AS balks,

          SUM(ps.sacrifice_hits_allowed) AS sacrifice_hits_allowed,
          SUM(ps.sacrifice_flies_allowed) AS sacrifice_flies_allowed,

          SUM(ps.stolen_bases_allowed) AS stolen_bases_allowed,
          SUM(ps.caught_stealing) AS caught_stealing,

          SUM(ps.passed_balls) AS passed_balls,

          SUM(CASE WHEN ps.win THEN 1 ELSE 0 END) AS wins,
          SUM(CASE WHEN ps.loss THEN 1 ELSE 0 END) AS losses,
          SUM(CASE WHEN ps.save THEN 1 ELSE 0 END) AS saves,

          SUM(CASE WHEN ps.game_started THEN 1 ELSE 0 END) AS games_started,
          SUM(CASE WHEN ps.complete_game THEN 1 ELSE 0 END) AS complete_games,

          ROUND(
              (SUM(ps.earned_runs) * 9.0) /
              NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
              2
          ) AS era,

          ROUND(
              (SUM(ps.walks_allowed) + SUM(ps.hits_allowed))::decimal /
              NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
              3
          ) AS whip,

          ROUND(
              SUM(ps.hits_allowed)::decimal /
              NULLIF(
                  SUM(ps.batters_faced)
                  - SUM(ps.walks_allowed)
                  - SUM(ps.hit_batters)
                  - SUM(ps.sacrifice_hits_allowed)
                  - SUM(ps.sacrifice_flies_allowed),
              0),
              3
          ) AS opponent_batting_avg,

          ROUND(
              (SUM(ps.strikeouts) * 9.0) /
              NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
              2
          ) AS k_per_9,

          ROUND(
              (SUM(ps.walks_allowed) * 9.0) /
              NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
              2
          ) AS bb_per_9

      FROM pitching_stats ps
      JOIN games g ON ps.game_id = g.game_id
      JOIN teams t ON g.home_team_id = t.team_id
      JOIN season_games sg ON sg.season = ps.season

      WHERE
          LOWER(g.game_type) = 'regular'
          AND t.league IN ('AL', 'NL')

      GROUP BY
          ps.player_id,
          ps.team_id,
          ps.season,
          sg.team_games

      HAVING
          SUM(ps.outs_pitched) >= 3 * sg.team_games;
  CREATE UNIQUE INDEX ON qualified_pitching_seasons (player_id, team_id, season);


  SELECT pg_temp.drop_view_or_matview('v_player_career_batting');
  CREATE MATERIALIZED VIEW v_player_career_batting AS
  SELECT
      p.player_id,
      p.first_name,
      p.last_name,
      SUM(bs.at_bats) as career_ab,
      SUM(bs.hits) as career_h,
      SUM(bs.home_runs) as career_hr,
      SUM(bs.rbis) as career_rbi,
      SUM(bs.runs) as career_r,
      SUM(bs.walks) as career_w,
      SUM(bs.strikeouts) as career_k,
      SUM(bs.stolen_bases) as career_sb,
      CASE WHEN SUM(bs.at_bats) > 0
           THEN ROUND(SUM(bs.hits)::DECIMAL / SUM(bs.at_bats), 3)
           ELSE 0 END as career_avg,
      CASE WHEN (SUM(bs.at_bats) + SUM(bs.walks) + SUM(bs.hit_by_pitch) + SUM(bs.sacrifice_flies)) > 0
           THEN ROUND((SUM(bs.hits) + SUM(bs.walks) + SUM(bs.hit_by_pitch))::DECIMAL /
                      (SUM(bs.at_bats) + SUM(bs.walks) + SUM(bs.hit_by_pitch) + SUM(bs.sacrifice_flies)), 3)
           ELSE 0 END as career_obp,
      CASE WHEN SUM(bs.at_bats) > 0
           THEN ROUND((SUM(bs.singles) + 2*SUM(bs.doubles) + 3*SUM(bs.triples) + 4*SUM(bs.home_runs))::DECIMAL / SUM(bs.at_bats), 3)
           ELSE 0 END as career_slg,
      COUNT(DISTINCT bs.season) as seasons,
      MIN(bs.season) as first_season,
      MAX(bs.season) as last_season
  FROM players p
  LEFT JOIN (
      -- Same regular-season/AL-NL filter as all_batting_seasons, so career
      -- and season totals stay consistent with each other.
      SELECT bs.*
      FROM batting_stats bs
      JOIN games g ON bs.game_id = g.game_id
      JOIN teams th ON g.home_team_id = th.team_id
      JOIN teams ta ON g.away_team_id = ta.team_id
      WHERE LOWER(g.game_type) = 'regular'
        AND th.league IN ('AL','NL')
        AND ta.league IN ('AL','NL')
  ) bs ON p.player_id = bs.player_id
  GROUP BY p.player_id, p.first_name, p.last_name;
  CREATE UNIQUE INDEX ON v_player_career_batting (player_id);
  COMMENT ON MATERIALIZED VIEW v_player_career_batting IS 'Career batting statistics aggregated by player';


  SELECT pg_temp.drop_view_or_matview('v_player_career_pitching');
  CREATE MATERIALIZED VIEW v_player_career_pitching AS
  SELECT
      p.player_id,
      p.first_name,
      p.last_name,
      SUM(ps.innings_pitched) as career_ip,
      SUM(ps.hits_allowed) as career_h,
      SUM(ps.home_runs_allowed) as career_hr,
      SUM(ps.runs_allowed) as career_r,
      SUM(ps.earned_runs) as career_er,
      SUM(ps.walks_allowed) as career_w,
      SUM(ps.strikeouts) as career_k,
      SUM(ps.win::INTEGER) as career_wins,
      SUM(ps.loss::INTEGER) as career_losses,
      SUM(ps.save::INTEGER) as career_saves,
      CASE WHEN SUM(ps.innings_pitched) > 0
           THEN ROUND((SUM(ps.earned_runs) * 9.0) / SUM(ps.innings_pitched), 2)
           ELSE 0 END as career_era,
      CASE WHEN SUM(ps.innings_pitched) > 0
           THEN ROUND((SUM(ps.walks_allowed) + SUM(ps.hits_allowed))::DECIMAL / SUM(ps.innings_pitched), 2)
           ELSE 0 END as career_whip,
      COUNT(DISTINCT ps.season) as seasons,
      MIN(ps.season) as first_season,
      MAX(ps.season) as last_season
  FROM players p
  LEFT JOIN (
      -- Same regular-season/AL-NL filter as all_pitching_seasons (home
      -- team's league only, matching that view's existing convention).
      SELECT ps.*
      FROM pitching_stats ps
      JOIN games g ON ps.game_id = g.game_id
      JOIN teams t ON g.home_team_id = t.team_id
      WHERE LOWER(g.game_type) = 'regular'
        AND t.league IN ('AL','NL')
  ) ps ON p.player_id = ps.player_id
  GROUP BY p.player_id, p.first_name, p.last_name;
  CREATE UNIQUE INDEX ON v_player_career_pitching (player_id);
  COMMENT ON MATERIALIZED VIEW v_player_career_pitching IS 'Career pitching statistics aggregated by player';
SQL

if [[ -n "${POSTGRES_READONLY_USER:-}" ]]; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
    GRANT SELECT ON
      all_batting_seasons, all_pitching_seasons,
      qualified_batting_seasons, qualified_pitching_seasons,
      v_player_career_batting, v_player_career_pitching
      TO "${POSTGRES_READONLY_USER}";
SQL
fi

echo "Materialized views created and refreshed."
