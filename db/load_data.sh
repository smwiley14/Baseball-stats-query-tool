#!/bin/bash

# Script to load all CSV data into the PostgreSQL database
# This script loads data in the correct order to respect foreign key constraints

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-retrosheet}"
DB_USER="${DB_USER:-baseball}"
DB_PASSWORD="${DB_PASSWORD:-baseball}"

export PGPASSWORD="$DB_PASSWORD"

echo "=========================================="
echo "Loading Baseball Stats Data"
echo "=========================================="
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Function to load CSV with error handling
load_csv() {
    local table=$1
    local file=$2
    local options=$3
    
    if [ ! -f "$file" ]; then
        echo "  ⚠️  File not found: $file"
        return 1
    fi
    
    echo "  Loading $table from $(basename $file)..."
    
    # Count lines (excluding header)
    local lines=$(tail -n +2 "$file" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$lines" -eq 0 ]; then
        echo "    ⚠️  File is empty, skipping"
        return 0
    fi
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY $table $options FROM '$file' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '')" 2>&1 | \
        grep -v "COPY" | grep -v "^$" || true
    
    echo "    ✓ Loaded $lines rows"
}

# Function to load CSV with custom SQL (for transformations)
load_csv_sql() {
    local sql=$1
    local file=$2
    
    if [ ! -f "$file" ]; then
        echo "  ⚠️  File not found: $file"
        return 1
    fi
    
    echo "  Loading via custom SQL from $(basename $file)..."
    
    local lines=$(tail -n +2 "$file" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$lines" -eq 0 ]; then
        echo "    ⚠️  File is empty, skipping"
        return 0
    fi
    
    # Create temp table and load
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f - <<EOF
$sql
\COPY temp_load FROM '$file' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');
EOF
    
    echo "    ✓ Processed $lines rows"
}

echo "Step 1: Loading Players..."
echo "----------------------------------------"

# Load players from rosters (most comprehensive)
if [ -d "data/processed/rosters" ]; then
    echo "  Loading players from roster files..."
    for roster_file in data/processed/rosters/*.csv; do
        if [ -f "$roster_file" ]; then
            # Clean the file to remove carriage returns if needed
            temp_file=$(mktemp)
            tr -d '\r' < "$roster_file" > "$temp_file"
            
            # Use a temp table approach since \COPY can't be used with ON CONFLICT directly
            # Handle carriage returns and encoding issues
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
CREATE TEMP TABLE IF NOT EXISTS temp_player_load (
    player_id VARCHAR(10), last_name VARCHAR(50), first_name VARCHAR(50),
    batting_hand CHAR(1), throwing_hand CHAR(1), team VARCHAR(5), position VARCHAR(10)
);
TRUNCATE temp_player_load;
\COPY temp_player_load FROM '$temp_file' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '', QUOTE '"', ESCAPE '"');
-- Handle duplicates by using DISTINCT ON to get one row per player_id
-- Prefer rows with more complete data
INSERT INTO players (player_id, last_name, first_name, batting_hand, throwing_hand)
SELECT DISTINCT ON (TRIM(player_id))
    TRIM(player_id), 
    TRIM(last_name), 
    TRIM(first_name), 
    TRIM(batting_hand), 
    TRIM(throwing_hand)
FROM temp_player_load
WHERE player_id IS NOT NULL AND TRIM(player_id) != ''
ORDER BY TRIM(player_id),
         CASE WHEN TRIM(last_name) IS NOT NULL AND TRIM(last_name) != '' THEN 0 ELSE 1 END,
         CASE WHEN TRIM(first_name) IS NOT NULL AND TRIM(first_name) != '' THEN 0 ELSE 1 END,
         CASE WHEN TRIM(batting_hand) IS NOT NULL AND TRIM(batting_hand) != '' THEN 0 ELSE 1 END,
         CASE WHEN TRIM(throwing_hand) IS NOT NULL AND TRIM(throwing_hand) != '' THEN 0 ELSE 1 END
ON CONFLICT (player_id) DO UPDATE SET
    last_name = COALESCE(NULLIF(TRIM(EXCLUDED.last_name), ''), players.last_name),
    first_name = COALESCE(NULLIF(TRIM(EXCLUDED.first_name), ''), players.first_name),
    batting_hand = COALESCE(NULLIF(TRIM(EXCLUDED.batting_hand), ''), players.batting_hand),
    throwing_hand = COALESCE(NULLIF(TRIM(EXCLUDED.throwing_hand), ''), players.throwing_hand);
EOF
            rm -f "$temp_file"
        fi
    done 2>&1 | grep -v "COPY" | grep -v "^$" | grep -v "TRUNCATE" | grep -v "CREATE" || true
    echo "  ✓ Players loaded"
fi

# Also load from allplayers.csv if available
if [ -f "data/allplayers.csv" ]; then
    echo "  Loading additional player data from allplayers.csv..."
    # Create temp table, load data, and insert in a single session (temp tables are session-scoped)
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
CREATE TEMP TABLE IF NOT EXISTS temp_load (
    id VARCHAR(10), last VARCHAR(50), first VARCHAR(50), 
    bat CHAR(1), throw CHAR(1), team VARCHAR(5), 
    g INTEGER, g_p INTEGER, g_sp INTEGER, g_rp INTEGER,
    g_c INTEGER, g_1b INTEGER, g_2b INTEGER, g_3b INTEGER,
    g_ss INTEGER, g_lf INTEGER, g_cf INTEGER, g_rf INTEGER,
    g_of INTEGER, g_dh INTEGER, g_ph INTEGER, g_pr INTEGER,
    first_g VARCHAR(20), last_g VARCHAR(20), season INTEGER
);
TRUNCATE temp_load;
\COPY temp_load FROM 'data/allplayers.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');

INSERT INTO players (player_id, first_name, last_name, batting_hand, throwing_hand)
SELECT DISTINCT ON (id)
    id, first, last, bat, throw
FROM temp_load
WHERE id IS NOT NULL AND id != ''
ORDER BY id,
         CASE WHEN first IS NOT NULL AND first != '' THEN 0 ELSE 1 END,
         CASE WHEN last IS NOT NULL AND last != '' THEN 0 ELSE 1 END,
         CASE WHEN bat IS NOT NULL AND bat != '' THEN 0 ELSE 1 END,
         CASE WHEN throw IS NOT NULL AND throw != '' THEN 0 ELSE 1 END
ON CONFLICT (player_id) DO UPDATE SET
    first_name = COALESCE(NULLIF(EXCLUDED.first_name, ''), players.first_name),
    last_name = COALESCE(NULLIF(EXCLUDED.last_name, ''), players.last_name),
    batting_hand = COALESCE(NULLIF(EXCLUDED.batting_hand, ''), players.batting_hand),
    throwing_hand = COALESCE(NULLIF(EXCLUDED.throwing_hand, ''), players.throwing_hand);
DROP TABLE temp_load;
EOF
    echo "  ✓ Additional player data loaded"
fi

echo ""
echo "Step 2: Loading Teams..."
echo "----------------------------------------"

# Extract teams from gameinfo.csv before loading games
# We'll load gameinfo into temp table and reuse it for games
if [ -f "data/gameinfo.csv" ]; then
    echo "  Extracting teams from gameinfo.csv..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
-- Create temp table to load gameinfo (will be reused in Step 3)
-- Use VARCHAR for attendance to handle "6500?" type values
CREATE TEMP TABLE IF NOT EXISTS temp_gameinfo_raw (
    gid VARCHAR(20), visteam VARCHAR(5), hometeam VARCHAR(5), site VARCHAR(10),
    date DATE, number INTEGER, starttime VARCHAR(10), daynight VARCHAR(10),
    innings INTEGER, tiebreaker VARCHAR(10), usedh VARCHAR(10), htbf VARCHAR(10),
    timeofgame INTEGER, attendance VARCHAR(20), fieldcond VARCHAR(20), precip VARCHAR(20),
    sky VARCHAR(20), temp VARCHAR(20), winddir VARCHAR(10), windspeed VARCHAR(20),
    oscorer VARCHAR(20), forfeit VARCHAR(10), suspend VARCHAR(10),
    umphome VARCHAR(10), ump1b VARCHAR(10), ump2b VARCHAR(10), ump3b VARCHAR(10),
    umplf VARCHAR(10), umprf VARCHAR(10), wp VARCHAR(10), lp VARCHAR(10),
    save VARCHAR(10), gametype VARCHAR(20), vruns INTEGER, hruns INTEGER,
    wteam VARCHAR(5), lteam VARCHAR(5), line VARCHAR(10), batteries VARCHAR(10),
    lineups VARCHAR(10), box VARCHAR(10), pbp VARCHAR(10), season INTEGER
);
TRUNCATE temp_gameinfo_raw;

-- Load gameinfo
\COPY temp_gameinfo_raw FROM 'data/gameinfo.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');

-- Create cleaned version with proper data types
DROP TABLE IF EXISTS temp_gameinfo;
CREATE TEMP TABLE temp_gameinfo AS
SELECT 
    gid, visteam, hometeam, site,
    date, number, starttime, daynight,
    innings, tiebreaker, usedh, htbf,
    timeofgame, 
    CASE 
        WHEN attendance ~ '^[0-9]+$' THEN attendance::INTEGER 
        WHEN attendance ~ '^[0-9]+[^0-9]' THEN REGEXP_REPLACE(attendance, '[^0-9].*', '')::INTEGER
        ELSE NULL 
    END as attendance,
    fieldcond, precip, sky, 
    CASE 
        WHEN temp ~ '^[0-9]+$' THEN temp::INTEGER 
        WHEN temp ~ '^[0-9]+[^0-9]' THEN REGEXP_REPLACE(temp, '[^0-9].*', '')::INTEGER
        WHEN LOWER(temp) IN ('unknown', '') THEN NULL
        ELSE NULL 
    END as temp, 
    winddir, 
    CASE 
        WHEN windspeed ~ '^[0-9]+$' THEN windspeed::INTEGER 
        WHEN windspeed ~ '^[0-9]+[^0-9]' THEN REGEXP_REPLACE(windspeed, '[^0-9].*', '')::INTEGER
        WHEN LOWER(windspeed) IN ('unknown', '') THEN NULL
        ELSE NULL 
    END as windspeed,
    oscorer, forfeit, suspend,
    umphome, ump1b, ump2b, ump3b,
    umplf, umprf, wp, lp, save, gametype, vruns, hruns,
    wteam, lteam, line, batteries,
    lineups, box, pbp, season
FROM temp_gameinfo_raw;
DROP TABLE temp_gameinfo_raw;

-- Extract unique teams
INSERT INTO teams (team_id, league, city, name)
SELECT DISTINCT hometeam, NULL, NULL, hometeam
FROM temp_gameinfo
WHERE hometeam IS NOT NULL AND hometeam != ''
ON CONFLICT (team_id) DO NOTHING;

INSERT INTO teams (team_id, league, city, name)
SELECT DISTINCT visteam, NULL, NULL, visteam
FROM temp_gameinfo
WHERE visteam IS NOT NULL AND visteam != ''
ON CONFLICT (team_id) DO NOTHING;

-- Extract unique parks (required for games foreign key)
INSERT INTO parks (park_id, name)
SELECT DISTINCT site, site
FROM temp_gameinfo
WHERE site IS NOT NULL AND site != ''
ON CONFLICT (park_id) DO NOTHING;

-- Extract unique umpires (required for games foreign key)
INSERT INTO umpires (umpire_id, name)
SELECT DISTINCT umphome, umphome
FROM temp_gameinfo
WHERE umphome IS NOT NULL AND umphome != ''
ON CONFLICT (umpire_id) DO NOTHING;

INSERT INTO umpires (umpire_id, name)
SELECT DISTINCT ump1b, ump1b
FROM temp_gameinfo
WHERE ump1b IS NOT NULL AND ump1b != ''
ON CONFLICT (umpire_id) DO NOTHING;

INSERT INTO umpires (umpire_id, name)
SELECT DISTINCT ump2b, ump2b
FROM temp_gameinfo
WHERE ump2b IS NOT NULL AND ump2b != ''
ON CONFLICT (umpire_id) DO NOTHING;

INSERT INTO umpires (umpire_id, name)
SELECT DISTINCT ump3b, ump3b
FROM temp_gameinfo
WHERE ump3b IS NOT NULL AND ump3b != ''
ON CONFLICT (umpire_id) DO NOTHING;

INSERT INTO umpires (umpire_id, name)
SELECT DISTINCT umplf, umplf
FROM temp_gameinfo
WHERE umplf IS NOT NULL AND umplf != ''
ON CONFLICT (umpire_id) DO NOTHING;

INSERT INTO umpires (umpire_id, name)
SELECT DISTINCT umprf, umprf
FROM temp_gameinfo
WHERE umprf IS NOT NULL AND umprf != ''
ON CONFLICT (umpire_id) DO NOTHING;
EOF
    echo "  ✓ Teams, parks, and umpires extracted (temp_gameinfo ready for games)"
fi

# Teams are already extracted from gameinfo.csv above
# If additional team data is needed, it should be loaded from TEAM files

echo "  ✓ Teams loaded"
echo ""

echo "Step 3: Loading Games..."
echo "----------------------------------------"

# Load from gameinfo.csv (simpler format)
# Temp tables are session-scoped, so we must create and use them in the same session
if [ -f "data/gameinfo.csv" ]; then
    echo "  Loading games from gameinfo.csv..."
    
    # Create temp table, load data, and insert in a single session
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
-- Create temp table to load gameinfo (raw version with VARCHAR for problematic fields)
CREATE TEMP TABLE IF NOT EXISTS temp_gameinfo_raw (
    gid VARCHAR(20), visteam VARCHAR(5), hometeam VARCHAR(5), site VARCHAR(10),
    date DATE, number INTEGER, starttime VARCHAR(10), daynight VARCHAR(10),
    innings INTEGER, tiebreaker VARCHAR(10), usedh VARCHAR(10), htbf VARCHAR(10),
    timeofgame INTEGER, attendance VARCHAR(20), fieldcond VARCHAR(20), precip VARCHAR(20),
    sky VARCHAR(20), temp VARCHAR(20), winddir VARCHAR(10), windspeed VARCHAR(20),
    oscorer VARCHAR(20), forfeit VARCHAR(10), suspend VARCHAR(10),
    umphome VARCHAR(10), ump1b VARCHAR(10), ump2b VARCHAR(10), ump3b VARCHAR(10),
    umplf VARCHAR(10), umprf VARCHAR(10), wp VARCHAR(10), lp VARCHAR(10),
    save VARCHAR(10), gametype VARCHAR(20), vruns INTEGER, hruns INTEGER,
    wteam VARCHAR(5), lteam VARCHAR(5), line VARCHAR(10), batteries VARCHAR(10),
    lineups VARCHAR(10), box VARCHAR(10), pbp VARCHAR(10), season INTEGER
);
TRUNCATE temp_gameinfo_raw;

-- Load gameinfo
\COPY temp_gameinfo_raw FROM 'data/gameinfo.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');

-- Create cleaned version with proper data types
DROP TABLE IF EXISTS temp_gameinfo;
CREATE TEMP TABLE temp_gameinfo AS
SELECT 
    gid, visteam, hometeam, site,
    date, number, starttime, daynight,
    innings, tiebreaker, usedh, htbf,
    timeofgame, 
    CASE 
        WHEN attendance ~ '^[0-9]+$' THEN attendance::INTEGER 
        WHEN attendance ~ '^[0-9]+[^0-9]' THEN REGEXP_REPLACE(attendance, '[^0-9].*', '')::INTEGER
        ELSE NULL 
    END as attendance,
    fieldcond, precip, sky, 
    CASE 
        WHEN temp ~ '^[0-9]+$' THEN temp::INTEGER 
        WHEN temp ~ '^[0-9]+[^0-9]' THEN REGEXP_REPLACE(temp, '[^0-9].*', '')::INTEGER
        WHEN LOWER(temp) IN ('unknown', '') THEN NULL
        ELSE NULL 
    END as temp, 
    winddir, 
    CASE 
        WHEN windspeed ~ '^[0-9]+$' THEN windspeed::INTEGER 
        WHEN windspeed ~ '^[0-9]+[^0-9]' THEN REGEXP_REPLACE(windspeed, '[^0-9].*', '')::INTEGER
        WHEN LOWER(windspeed) IN ('unknown', '') THEN NULL
        ELSE NULL 
    END as windspeed,
    oscorer, forfeit, suspend,
    umphome, ump1b, ump2b, ump3b,
    umplf, umprf, wp, lp, save, gametype, vruns, hruns,
    wteam, lteam, line, batteries,
    lineups, box, pbp, season
FROM temp_gameinfo_raw;
DROP TABLE temp_gameinfo_raw;

-- Insert games from temp_gameinfo
INSERT INTO games (
    game_id, game_date, season, game_number, day_of_week, start_time, daynight, dh_flag,
    home_team_id, away_team_id, park_id, home_score, away_score, home_hits, away_hits,
    home_errors, away_errors, innings, minutes, attendance,
    temperature, wind_direction, wind_speed, field_condition, precipitation, sky,
    winning_pitcher_id, losing_pitcher_id, save_pitcher_id,
    home_plate_umpire_id, first_base_umpire_id, second_base_umpire_id,
    third_base_umpire_id, game_type, forfeit_flag, suspend_flag
)
SELECT 
    gid, date, season, number, NULL, starttime, 
    CASE WHEN daynight = 'day' THEN 'D' WHEN daynight = 'night' THEN 'N' ELSE NULL END,
    CASE WHEN usedh = 'true' THEN 'T' ELSE 'F' END,
    hometeam, visteam, site, hruns, vruns, NULL, NULL, NULL, NULL, innings, timeofgame, attendance,
    temp, winddir, windspeed, fieldcond, precip, sky,
    wp, lp, save,
    umphome, ump1b, ump2b, ump3b, gametype,
    CASE WHEN forfeit IS NOT NULL AND forfeit != '' THEN 'T' ELSE 'F' END,
    CASE WHEN suspend IS NOT NULL AND suspend != '' THEN 'T' ELSE 'F' END
FROM temp_gameinfo
ON CONFLICT (game_id) DO UPDATE SET
    game_date = EXCLUDED.game_date,
    home_score = EXCLUDED.home_score,
    away_score = EXCLUDED.away_score;
DROP TABLE temp_gameinfo;
EOF
    echo "  ✓ Games loaded from gameinfo.csv"
fi

# Also load from processed games if available (more detailed)
if [ -d "data/processed/games" ]; then
    echo "  Loading additional game data from processed games..."
    for game_file in data/processed/games/*.csv; do
        if [ -f "$game_file" ]; then
            # This would need more complex mapping - for now we'll skip if gameinfo was loaded
            if [ ! -f "data/gameinfo.csv" ]; then
                echo "    Loading $(basename $game_file)..."
                # Would need to map the 84 columns from cwgame output
                # This is complex, so we'll focus on gameinfo.csv for now
            fi
        fi
    done
fi

echo ""
echo "Step 4: Loading Rosters..."
echo "----------------------------------------"

if [ -d "data/processed/rosters" ]; then
    echo "  Loading rosters..."
    
    for roster_file in data/processed/rosters/*.csv; do
        if [ -f "$roster_file" ]; then
            year=$(basename "$roster_file" | sed 's/rosters_\([0-9]*\)\.csv/\1/')
            if [ -n "$year" ] && [ "$year" != "$(basename $roster_file)" ]; then
                # Clean the file to remove carriage returns if needed
                temp_file=$(mktemp)
                tr -d '\r' < "$roster_file" > "$temp_file"
                
                # Create temp table, load, and insert in a single session (temp tables are session-scoped)
                psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
CREATE TEMP TABLE IF NOT EXISTS temp_roster (
    player_id VARCHAR(10), last_name VARCHAR(50), first_name VARCHAR(50),
    batting_hand CHAR(1), throwing_hand CHAR(1), team VARCHAR(5), position VARCHAR(10)
);
TRUNCATE temp_roster;
\COPY temp_roster FROM '$temp_file' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '', QUOTE '"', ESCAPE '"');
INSERT INTO rosters (player_id, team_id, season, position)
SELECT player_id, team, $year::INTEGER, position
FROM temp_roster
WHERE player_id IS NOT NULL AND team IS NOT NULL
ON CONFLICT (player_id, team_id, season) DO UPDATE SET position = EXCLUDED.position;
DROP TABLE temp_roster;
EOF
                rm -f "$temp_file"
            fi
        fi
    done 2>&1 | grep -v "COPY" | grep -v "^$" | grep -v "TRUNCATE" | grep -v "CREATE" | grep -v "DROP" || true
    
    echo "  ✓ Rosters loaded"
fi

echo ""
echo "Step 5: Loading Batting Stats..."
echo "----------------------------------------"

if [ -f "data/batting.csv" ]; then
    echo "  Loading batting statistics..."
    # Create temp table, load data, and insert in a single session (temp tables are session-scoped)
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
CREATE TEMP TABLE IF NOT EXISTS temp_load (
    gid VARCHAR(20), id VARCHAR(10), team VARCHAR(5), b_lp INTEGER, b_seq INTEGER,
    stattype VARCHAR(10), b_pa INTEGER, b_ab INTEGER, b_r INTEGER, b_h INTEGER,
    b_d INTEGER, b_t INTEGER, b_hr INTEGER, b_rbi INTEGER, b_sh INTEGER, b_sf INTEGER,
    b_hbp INTEGER, b_w INTEGER, b_iw INTEGER, b_k INTEGER, b_sb INTEGER, b_cs INTEGER,
    b_gdp INTEGER, b_xi INTEGER, b_roe INTEGER, dh VARCHAR(10), ph VARCHAR(10),
    pr VARCHAR(10), date DATE, number INTEGER, site VARCHAR(10), vishome VARCHAR(10),
    opp VARCHAR(5), win INTEGER, loss INTEGER, tie INTEGER, gametype VARCHAR(20),
    box VARCHAR(10), pbp VARCHAR(10)
);
TRUNCATE temp_load;
\COPY temp_load FROM 'data/batting.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');

INSERT INTO batting_stats (
    game_id, player_id, team_id, season, game_date,
    plate_appearances, at_bats, hits, singles, doubles, triples, home_runs,
    runs, rbis, walks, intentional_walks, strikeouts, hit_by_pitch,
    sacrifice_hits, sacrifice_flies, stolen_bases, caught_stealing,
    grounded_into_double_play, reached_on_error
)
SELECT DISTINCT ON (gid, id, team)
    gid, id, team, 
    EXTRACT(YEAR FROM date)::INTEGER as season,
    date,
    COALESCE(b_pa, 0), COALESCE(b_ab, 0), COALESCE(b_h, 0),
    COALESCE(b_h - b_d - b_t - b_hr, 0) as singles,
    COALESCE(b_d, 0), COALESCE(b_t, 0), COALESCE(b_hr, 0),
    COALESCE(b_r, 0), COALESCE(b_rbi, 0),
    COALESCE(b_w, 0), COALESCE(b_iw, 0), COALESCE(b_k, 0), COALESCE(b_hbp, 0),
    COALESCE(b_sh, 0), COALESCE(b_sf, 0),
    COALESCE(b_sb, 0), COALESCE(b_cs, 0),
    COALESCE(b_gdp, 0), COALESCE(b_roe, 0)
FROM temp_load
WHERE stattype = 'value' AND b_ab IS NOT NULL
ORDER BY gid, id, team, date DESC
ON CONFLICT (game_id, player_id, team_id) DO UPDATE SET
    plate_appearances = EXCLUDED.plate_appearances,
    at_bats = EXCLUDED.at_bats,
    hits = EXCLUDED.hits;
DROP TABLE temp_load;
EOF
    echo "  ✓ Batting stats loaded"
fi

echo ""
echo "Step 6: Loading Pitching Stats..."
echo "----------------------------------------"

if [ -f "data/pitching.csv" ]; then
    echo "  Loading pitching statistics..."
    # Create temp table, load data, and insert in a single session (temp tables are session-scoped)
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
CREATE TEMP TABLE IF NOT EXISTS temp_load (
    gid VARCHAR(20), id VARCHAR(10), team VARCHAR(5), p_seq INTEGER, stattype VARCHAR(10),
    p_ipouts INTEGER, p_noout INTEGER, p_bfp INTEGER, p_h INTEGER, p_d INTEGER, p_t INTEGER,
    p_hr INTEGER, p_r INTEGER, p_er INTEGER, p_w INTEGER, p_iw INTEGER, p_k INTEGER,
    p_hbp INTEGER, p_wp INTEGER, p_bk INTEGER, p_sh INTEGER, p_sf INTEGER, p_sb INTEGER,
    p_cs INTEGER, p_pb INTEGER, wp INTEGER, lp INTEGER, save INTEGER, p_gs INTEGER,
    p_gf INTEGER, p_cg INTEGER, date DATE, number INTEGER, site VARCHAR(10),
    vishome VARCHAR(10), opp VARCHAR(5), win INTEGER, loss INTEGER, tie INTEGER,
    gametype VARCHAR(20), box VARCHAR(10), pbp VARCHAR(10)
);
TRUNCATE temp_load;
\COPY temp_load FROM 'data/pitching.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');

INSERT INTO pitching_stats (
    game_id, player_id, team_id, season, game_date,
    outs_pitched, innings_pitched, batters_faced,
    hits_allowed, doubles_allowed, triples_allowed, home_runs_allowed,
    runs_allowed, earned_runs, walks_allowed, intentional_walks, strikeouts, hit_batters,
    wild_pitches, balks, sacrifice_hits_allowed, sacrifice_flies_allowed,
    stolen_bases_allowed, caught_stealing, passed_balls,
    win, loss, save, game_started, game_finished, complete_game
)
SELECT DISTINCT ON (gid, id, team)
    gid, id, team,
    EXTRACT(YEAR FROM date)::INTEGER as season,
    date,
    COALESCE(p_ipouts, 0),
    ROUND(COALESCE(p_ipouts, 0)::DECIMAL / 3.0, 1) as innings_pitched,
    COALESCE(p_bfp, 0),
    COALESCE(p_h, 0), COALESCE(p_d, 0), COALESCE(p_t, 0), COALESCE(p_hr, 0),
    COALESCE(p_r, 0), COALESCE(p_er, 0),
    COALESCE(p_w, 0), COALESCE(p_iw, 0), COALESCE(p_k, 0), COALESCE(p_hbp, 0),
    COALESCE(p_wp, 0), COALESCE(p_bk, 0),
    COALESCE(p_sh, 0), COALESCE(p_sf, 0),
    COALESCE(p_sb, 0), COALESCE(p_cs, 0), COALESCE(p_pb, 0),
    COALESCE(win, 0)::BOOLEAN, COALESCE(loss, 0)::BOOLEAN, COALESCE(save, 0)::BOOLEAN,
    COALESCE(p_gs, 0)::BOOLEAN, COALESCE(p_gf, 0)::BOOLEAN, COALESCE(p_cg, 0)::BOOLEAN
FROM temp_load
WHERE stattype = 'value' AND p_ipouts IS NOT NULL
ORDER BY gid, id, team, date DESC
ON CONFLICT (game_id, player_id, team_id) DO UPDATE SET
    outs_pitched = EXCLUDED.outs_pitched,
    innings_pitched = EXCLUDED.innings_pitched;
DROP TABLE temp_load;
EOF
    echo "  ✓ Pitching stats loaded"
fi

echo ""
echo "Step 7: Loading Fielding Stats..."
echo "----------------------------------------"

if [ -f "data/fielding.csv" ]; then
    echo "  Loading fielding statistics..."
    # Create temp table, load data, and insert in a single session (temp tables are session-scoped)
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
CREATE TEMP TABLE IF NOT EXISTS temp_load (
    gid VARCHAR(20), id VARCHAR(10), team VARCHAR(5), d_seq INTEGER, d_pos VARCHAR(10),
    stattype VARCHAR(10), d_ifouts INTEGER, d_po INTEGER, d_a INTEGER, d_e INTEGER,
    d_dp INTEGER, d_tp INTEGER, d_pb INTEGER, d_wp INTEGER, d_sb INTEGER, d_cs INTEGER,
    d_gs INTEGER, date DATE, number INTEGER, site VARCHAR(10), vishome VARCHAR(10),
    opp VARCHAR(5), win INTEGER, loss INTEGER, tie INTEGER, gametype VARCHAR(20),
    box VARCHAR(10), pbp VARCHAR(10)
);
TRUNCATE temp_load;
\COPY temp_load FROM 'data/fielding.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');

INSERT INTO fielding_stats (
    game_id, player_id, team_id, position, season, game_date,
    putouts, assists, errors, double_plays, triple_plays,
    passed_balls, wild_pitches, stolen_bases_allowed, caught_stealing, games_started
)
SELECT DISTINCT ON (gid, id, team, position_calc)
    gid, id, team, position_calc as position,
    EXTRACT(YEAR FROM date)::INTEGER as season,
    date,
    COALESCE(d_po, 0), COALESCE(d_a, 0), COALESCE(d_e, 0),
    COALESCE(d_dp, 0), COALESCE(d_tp, 0),
    COALESCE(d_pb, 0), COALESCE(d_wp, 0),
    COALESCE(d_sb, 0), COALESCE(d_cs, 0), COALESCE(d_gs, 0)
FROM (
    SELECT 
        gid, id, team, date,
        CASE 
            WHEN d_pos ~ '^[0-9]+$' THEN d_pos::INTEGER 
            ELSE NULL 
        END as position_calc,
        d_po, d_a, d_e, d_dp, d_tp, d_pb, d_wp, d_sb, d_cs, d_gs
    FROM temp_load
    WHERE stattype = 'value' AND d_pos IS NOT NULL AND d_pos != '?' AND d_pos ~ '^[0-9]+$'
) t
WHERE position_calc IS NOT NULL
ORDER BY gid, id, team, position_calc, date DESC
ON CONFLICT (game_id, player_id, team_id, position) DO UPDATE SET
    putouts = EXCLUDED.putouts,
    assists = EXCLUDED.assists,
    errors = EXCLUDED.errors;
DROP TABLE temp_load;
EOF
    echo "  ✓ Fielding stats loaded"
fi

echo ""
echo "Step 8: Loading Team Game Stats..."
echo "----------------------------------------"

if [ -f "data/teamstats.csv" ]; then
    echo "  Loading team game statistics..."
    # This is complex due to many columns - simplified version
    echo "  ⚠️  Team stats loading requires custom mapping (many columns)"
    echo "  See db/load_team_stats.sql for detailed implementation"
fi

echo ""
echo "Step 9: Updating Calculated Fields..."
echo "----------------------------------------"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
-- Update batting averages, OBP, SLG, OPS
UPDATE batting_stats
SET 
    batting_average = CASE WHEN at_bats > 0 THEN ROUND(hits::DECIMAL / at_bats, 3) ELSE 0 END,
    on_base_percentage = CASE 
        WHEN (at_bats + walks + hit_by_pitch + sacrifice_flies) > 0 
        THEN ROUND((hits + walks + hit_by_pitch)::DECIMAL / 
                   (at_bats + walks + hit_by_pitch + sacrifice_flies), 3)
        ELSE 0 END,
    slugging_percentage = CASE 
        WHEN at_bats > 0 
        THEN ROUND((singles + 2*doubles + 3*triples + 4*home_runs)::DECIMAL / at_bats, 3)
        ELSE 0 END
WHERE at_bats > 0;

UPDATE batting_stats
SET ops = on_base_percentage + slugging_percentage
WHERE on_base_percentage IS NOT NULL AND slugging_percentage IS NOT NULL;

-- Update ERA and WHIP for pitchers
UPDATE pitching_stats
SET 
    era = CASE 
        WHEN innings_pitched > 0 
        THEN ROUND((earned_runs * 9.0) / innings_pitched, 2)
        ELSE 0 END,
    whip = CASE 
        WHEN innings_pitched > 0 
        THEN ROUND((walks_allowed + hits_allowed)::DECIMAL / innings_pitched, 2)
        ELSE 0 END
WHERE innings_pitched > 0;

-- Update fielding percentage
UPDATE fielding_stats
SET 
    chances = putouts + assists + errors,
    fielding_percentage = CASE 
        WHEN (putouts + assists + errors) > 0 
        THEN ROUND((putouts + assists)::DECIMAL / (putouts + assists + errors), 3)
        ELSE 0 END
WHERE putouts + assists + errors > 0;
EOF

echo "  ✓ Calculated fields updated"

echo ""
echo "Step 10: Computing Player Seasons..."
echo "----------------------------------------"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
-- Compute player_seasons from aggregated stats
INSERT INTO player_seasons (player_id, season, team_id, games, first_game_date, last_game_date)
SELECT 
    player_id,
    season,
    team_id,
    COUNT(DISTINCT game_id) as games,
    MIN(game_date) as first_game_date,
    MAX(game_date) as last_game_date
FROM (
    SELECT player_id, season, team_id, game_id, game_date FROM batting_stats
    UNION
    SELECT player_id, season, team_id, game_id, game_date FROM pitching_stats
    UNION
    SELECT player_id, season, team_id, game_id, game_date FROM fielding_stats
) all_stats
WHERE player_id IS NOT NULL AND season IS NOT NULL AND team_id IS NOT NULL
GROUP BY player_id, season, team_id
ON CONFLICT (player_id, season, team_id) DO UPDATE SET
    games = EXCLUDED.games,
    first_game_date = EXCLUDED.first_game_date,
    last_game_date = EXCLUDED.last_game_date;

-- Update games by position from fielding_stats
UPDATE player_seasons ps
SET 
    games_catcher = COALESCE(fs.games_catcher, 0),
    games_first_base = COALESCE(fs.games_first_base, 0),
    games_second_base = COALESCE(fs.games_second_base, 0),
    games_third_base = COALESCE(fs.games_third_base, 0),
    games_shortstop = COALESCE(fs.games_shortstop, 0),
    games_left_field = COALESCE(fs.games_left_field, 0),
    games_center_field = COALESCE(fs.games_center_field, 0),
    games_right_field = COALESCE(fs.games_right_field, 0)
FROM (
    SELECT 
        player_id, season, team_id,
        SUM(CASE WHEN position = 2 THEN 1 ELSE 0 END) as games_catcher,
        SUM(CASE WHEN position = 3 THEN 1 ELSE 0 END) as games_first_base,
        SUM(CASE WHEN position = 4 THEN 1 ELSE 0 END) as games_second_base,
        SUM(CASE WHEN position = 5 THEN 1 ELSE 0 END) as games_third_base,
        SUM(CASE WHEN position = 6 THEN 1 ELSE 0 END) as games_shortstop,
        SUM(CASE WHEN position = 7 THEN 1 ELSE 0 END) as games_left_field,
        SUM(CASE WHEN position = 8 THEN 1 ELSE 0 END) as games_center_field,
        SUM(CASE WHEN position = 9 THEN 1 ELSE 0 END) as games_right_field
    FROM fielding_stats
    WHERE position IS NOT NULL
    GROUP BY player_id, season, team_id
) fs
WHERE ps.player_id = fs.player_id 
  AND ps.season = fs.season 
  AND ps.team_id = fs.team_id;

-- Update games_pitched from pitching_stats
UPDATE player_seasons ps
SET games_pitched = COALESCE(pstats.games_pitched, 0),
    games_started_pitcher = COALESCE(pstats.games_started, 0),
    games_relief = COALESCE(pstats.games_relief, 0)
FROM (
    SELECT 
        player_id, season, team_id,
        COUNT(DISTINCT game_id) as games_pitched,
        SUM(CASE WHEN game_started THEN 1 ELSE 0 END) as games_started,
        SUM(CASE WHEN NOT game_started THEN 1 ELSE 0 END) as games_relief
    FROM pitching_stats
    GROUP BY player_id, season, team_id
) pstats
WHERE ps.player_id = pstats.player_id 
  AND ps.season = pstats.season 
  AND ps.team_id = pstats.team_id;
EOF

echo "  ✓ Player seasons computed"

echo ""
echo "Step 11: Computing Team Game Stats..."
echo "----------------------------------------"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
-- Compute team_game_stats by aggregating from batting_stats, pitching_stats, fielding_stats
INSERT INTO team_game_stats (game_id, team_id, home_away, season, game_date)
SELECT DISTINCT
    g.game_id,
    bs.team_id,
    CASE WHEN g.home_team_id = bs.team_id THEN 'H' ELSE 'A' END as home_away,
    bs.season,
    bs.game_date
FROM batting_stats bs
JOIN games g ON bs.game_id = g.game_id
WHERE bs.game_id IS NOT NULL AND bs.team_id IS NOT NULL
ON CONFLICT (game_id, team_id) DO NOTHING;

-- Update team batting stats
UPDATE team_game_stats tgs
SET 
    team_pa = COALESCE(bat.team_pa, 0),
    team_ab = COALESCE(bat.team_ab, 0),
    team_r = COALESCE(bat.team_r, 0),
    team_h = COALESCE(bat.team_h, 0),
    team_d = COALESCE(bat.team_d, 0),
    team_t = COALESCE(bat.team_t, 0),
    team_hr = COALESCE(bat.team_hr, 0),
    team_rbi = COALESCE(bat.team_rbi, 0),
    team_sh = COALESCE(bat.team_sh, 0),
    team_sf = COALESCE(bat.team_sf, 0),
    team_hbp = COALESCE(bat.team_hbp, 0),
    team_w = COALESCE(bat.team_w, 0),
    team_iw = COALESCE(bat.team_iw, 0),
    team_k = COALESCE(bat.team_k, 0),
    team_sb = COALESCE(bat.team_sb, 0),
    team_cs = COALESCE(bat.team_cs, 0),
    team_gdp = COALESCE(bat.team_gdp, 0)
FROM (
    SELECT 
        game_id, team_id,
        SUM(plate_appearances) as team_pa,
        SUM(at_bats) as team_ab,
        SUM(runs) as team_r,
        SUM(hits) as team_h,
        SUM(doubles) as team_d,
        SUM(triples) as team_t,
        SUM(home_runs) as team_hr,
        SUM(rbis) as team_rbi,
        SUM(sacrifice_hits) as team_sh,
        SUM(sacrifice_flies) as team_sf,
        SUM(hit_by_pitch) as team_hbp,
        SUM(walks) as team_w,
        SUM(intentional_walks) as team_iw,
        SUM(strikeouts) as team_k,
        SUM(stolen_bases) as team_sb,
        SUM(caught_stealing) as team_cs,
        SUM(grounded_into_double_play) as team_gdp
    FROM batting_stats
    GROUP BY game_id, team_id
) bat
WHERE tgs.game_id = bat.game_id AND tgs.team_id = bat.team_id;

-- Update team pitching stats
UPDATE team_game_stats tgs
SET 
    team_ipouts = COALESCE(pit.team_ipouts, 0),
    team_bfp = COALESCE(pit.team_bfp, 0),
    team_p_h = COALESCE(pit.team_p_h, 0),
    team_p_d = COALESCE(pit.team_p_d, 0),
    team_p_t = COALESCE(pit.team_p_t, 0),
    team_p_hr = COALESCE(pit.team_p_hr, 0),
    team_p_r = COALESCE(pit.team_p_r, 0),
    team_p_er = COALESCE(pit.team_p_er, 0),
    team_p_w = COALESCE(pit.team_p_w, 0),
    team_p_iw = COALESCE(pit.team_p_iw, 0),
    team_p_k = COALESCE(pit.team_p_k, 0),
    team_p_hbp = COALESCE(pit.team_p_hbp, 0),
    team_p_wp = COALESCE(pit.team_p_wp, 0),
    team_p_bk = COALESCE(pit.team_p_bk, 0)
FROM (
    SELECT 
        game_id, team_id,
        SUM(outs_pitched) as team_ipouts,
        SUM(batters_faced) as team_bfp,
        SUM(hits_allowed) as team_p_h,
        SUM(doubles_allowed) as team_p_d,
        SUM(triples_allowed) as team_p_t,
        SUM(home_runs_allowed) as team_p_hr,
        SUM(runs_allowed) as team_p_r,
        SUM(earned_runs) as team_p_er,
        SUM(walks_allowed) as team_p_w,
        SUM(intentional_walks) as team_p_iw,
        SUM(strikeouts) as team_p_k,
        SUM(hit_batters) as team_p_hbp,
        SUM(wild_pitches) as team_p_wp,
        SUM(balks) as team_p_bk
    FROM pitching_stats
    GROUP BY game_id, team_id
) pit
WHERE tgs.game_id = pit.game_id AND tgs.team_id = pit.team_id;

-- Update team fielding stats
UPDATE team_game_stats tgs
SET 
    team_po = COALESCE(fld.team_po, 0),
    team_a = COALESCE(fld.team_a, 0),
    team_e = COALESCE(fld.team_e, 0),
    team_dp = COALESCE(fld.team_dp, 0),
    team_tp = COALESCE(fld.team_tp, 0)
FROM (
    SELECT 
        game_id, team_id,
        SUM(putouts) as team_po,
        SUM(assists) as team_a,
        SUM(errors) as team_e,
        SUM(double_plays) as team_dp,
        SUM(triple_plays) as team_tp
    FROM fielding_stats
    GROUP BY game_id, team_id
) fld
WHERE tgs.game_id = fld.game_id AND tgs.team_id = fld.team_id;
EOF

echo "  ✓ Team game stats computed"

echo ""
echo "=========================================="
echo "Data Loading Complete!"
echo "=========================================="
echo ""
echo "Summary:"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT 
    'Players: ' || COUNT(*) FROM players
UNION ALL
SELECT 
    'Teams: ' || COUNT(*) FROM teams
UNION ALL
SELECT 
    'Games: ' || COUNT(*) FROM games
UNION ALL
SELECT 
    'Batting Stats: ' || COUNT(*) FROM batting_stats
UNION ALL
SELECT 
    'Pitching Stats: ' || COUNT(*) FROM pitching_stats
UNION ALL
SELECT 
    'Fielding Stats: ' || COUNT(*) FROM fielding_stats
UNION ALL
SELECT 
    'Rosters: ' || COUNT(*) FROM rosters
UNION ALL
SELECT 
    'Player Seasons: ' || COUNT(*) FROM player_seasons
UNION ALL
SELECT 
    'Team Game Stats: ' || COUNT(*) FROM team_game_stats
UNION ALL
SELECT 
    'Game Lineups: ' || COUNT(*) FROM game_lineups;
"

unset PGPASSWORD

