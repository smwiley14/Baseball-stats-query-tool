-- Retrosheet Database Initialization
-- PostgreSQL-compatible schema
-- 
-- NOTE: This is a simplified schema. For a comprehensive schema with
-- optimized structure for stats queries, see schema.sql
--
-- To use the full schema, run: psql -d retrosheet -f schema.sql

-- Simple schema for basic operations
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    bats CHAR(1),
    throws CHAR(1)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    league TEXT,
    city TEXT,
    name TEXT
);

CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    game_date DATE,
    season INT,
    home_team TEXT REFERENCES teams(team_id),
    away_team TEXT REFERENCES teams(team_id),
    home_score INT,
    away_score INT,
    venue TEXT
);

CREATE TABLE IF NOT EXISTS rosters (
    player_id TEXT REFERENCES players(player_id),
    team_id TEXT REFERENCES teams(team_id),
    start_date DATE,
    end_date DATE,
    PRIMARY KEY (player_id, team_id, start_date)
);

CREATE TABLE IF NOT EXISTS appearances (
    game_id TEXT REFERENCES games(game_id),
    player_id TEXT REFERENCES players(player_id),
    team_id TEXT REFERENCES teams(team_id),
    role TEXT,
    PRIMARY KEY (game_id, player_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_pk SERIAL PRIMARY KEY,
    game_id TEXT REFERENCES games(game_id),
    inning INT,
    batting_team TEXT REFERENCES teams(team_id),
    batter TEXT REFERENCES players(player_id),
    pitcher TEXT REFERENCES players(player_id),
    event_type TEXT,
    hit_value INT,
    rbi INT,
    outs_on_play INT,
    description TEXT
);
