#!/bin/bash

# Script to load play-by-play events from processed event files
# This is separate because events can be very large

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
echo "Loading Play-by-Play Events"
echo "=========================================="
echo ""

if [ ! -d "data/processed/events" ]; then
    echo "  ⚠️  No events directory found"
    exit 1
fi

# Load events from processed files
# Note: This is a simplified version - the full event table has 97 columns
# You may want to load only specific columns or use a staging table

echo "Loading events (this may take a while)..."
echo ""

for event_file in data/processed/events/*.csv; do
    if [ -f "$event_file" ]; then
        year=$(basename "$event_file" | sed 's/events_\([0-9]*\)\.csv/\1/')
        echo "  Loading events for $year from $(basename $event_file)..."
        
        # Count lines
        lines=$(tail -n +2 "$event_file" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$lines" -eq 0 ]; then
            echo "    ⚠️  File is empty, skipping"
            continue
        fi
        
        # Load into staging table first, then insert with proper mapping
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
-- Create staging table for events
CREATE TEMP TABLE IF NOT EXISTS temp_events_staging (
    "GAME_ID" VARCHAR(20),
    "AWAY_TEAM_ID" VARCHAR(5),
    "INN_CT" INTEGER,
    "BAT_HOME_ID" INTEGER,
    "OUTS_CT" INTEGER,
    "BALLS_CT" INTEGER,
    "STRIKES_CT" INTEGER,
    "PITCH_SEQ_TX" TEXT,
    "AWAY_SCORE_CT" INTEGER,
    "HOME_SCORE_CT" INTEGER,
    "BAT_ID" VARCHAR(10),
    "BAT_HAND_CD" CHAR(1),
    "RESP_BAT_ID" VARCHAR(10),
    "RESP_BAT_HAND_CD" CHAR(1),
    "PIT_ID" VARCHAR(10),
    "PIT_HAND_CD" CHAR(1),
    "RESP_PIT_ID" VARCHAR(10),
    "RESP_PIT_HAND_CD" CHAR(1),
    "POS2_FLD_ID" VARCHAR(10),
    "POS3_FLD_ID" VARCHAR(10),
    "POS4_FLD_ID" VARCHAR(10),
    "POS5_FLD_ID" VARCHAR(10),
    "POS6_FLD_ID" VARCHAR(10),
    "POS7_FLD_ID" VARCHAR(10),
    "POS8_FLD_ID" VARCHAR(10),
    "POS9_FLD_ID" VARCHAR(10),
    "BASE1_RUN_ID" VARCHAR(10),
    "BASE2_RUN_ID" VARCHAR(10),
    "BASE3_RUN_ID" VARCHAR(10),
    "EVENT_TX" TEXT,
    "LEADOFF_FL" CHAR(1),
    "PH_FL" CHAR(1),
    "BAT_FLD_CD" VARCHAR(10),
    "BAT_LINEUP_ID" INTEGER,
    "EVENT_CD" INTEGER,
    "BAT_EVENT_FL" CHAR(1),
    "AB_FL" CHAR(1),
    "H_CD" INTEGER,
    "SH_FL" CHAR(1),
    "SF_FL" CHAR(1),
    "EVENT_OUTS_CT" INTEGER,
    "DP_FL" CHAR(1),
    "TP_FL" CHAR(1),
    "RBI_CT" INTEGER,
    "WP_FL" CHAR(1),
    "PB_FL" CHAR(1),
    "FLD_CD" VARCHAR(10),
    "BATTEDBALL_CD" VARCHAR(10),
    "BUNT_FL" CHAR(1),
    "FOUL_FL" CHAR(1),
    "BATTEDBALL_LOC_TX" TEXT,
    "ERR_CT" INTEGER,
    "ERR1_FLD_CD" VARCHAR(10),
    "ERR1_CD" VARCHAR(10),
    "ERR2_FLD_CD" VARCHAR(10),
    "ERR2_CD" VARCHAR(10),
    "ERR3_FLD_CD" VARCHAR(10),
    "ERR3_CD" VARCHAR(10),
    "BAT_DEST_ID" INTEGER,
    "RUN1_DEST_ID" INTEGER,
    "RUN2_DEST_ID" INTEGER,
    "RUN3_DEST_ID" INTEGER,
    "BAT_PLAY_TX" TEXT,
    "RUN1_PLAY_TX" TEXT,
    "RUN2_PLAY_TX" TEXT,
    "RUN3_PLAY_TX" TEXT,
    "RUN1_SB_FL" CHAR(1),
    "RUN2_SB_FL" CHAR(1),
    "RUN3_SB_FL" CHAR(1),
    "RUN1_CS_FL" CHAR(1),
    "RUN2_CS_FL" CHAR(1),
    "RUN3_CS_FL" CHAR(1),
    "RUN1_PK_FL" CHAR(1),
    "RUN2_PK_FL" CHAR(1),
    "RUN3_PK_FL" CHAR(1),
    "RUN1_RESP_PIT_ID" VARCHAR(10),
    "RUN2_RESP_PIT_ID" VARCHAR(10),
    "RUN3_RESP_PIT_ID" VARCHAR(10),
    "GAME_NEW_FL" CHAR(1),
    "GAME_END_FL" CHAR(1),
    "PR_RUN1_FL" CHAR(1),
    "PR_RUN2_FL" CHAR(1),
    "PR_RUN3_FL" CHAR(1),
    "REMOVED_FOR_PR_RUN1_ID" VARCHAR(10),
    "REMOVED_FOR_PR_RUN2_ID" VARCHAR(10),
    "REMOVED_FOR_PR_RUN3_ID" VARCHAR(10),
    "REMOVED_FOR_PH_BAT_ID" VARCHAR(10),
    "REMOVED_FOR_PH_BAT_FLD_CD" VARCHAR(10),
    "PO1_FLD_CD" VARCHAR(10),
    "PO2_FLD_CD" VARCHAR(10),
    "PO3_FLD_CD" VARCHAR(10),
    "ASS1_FLD_CD" VARCHAR(10),
    "ASS2_FLD_CD" VARCHAR(10),
    "ASS3_FLD_CD" VARCHAR(10),
    "ASS4_FLD_CD" VARCHAR(10),
    "ASS5_FLD_CD" VARCHAR(10),
    "EVENT_ID" INTEGER
);

TRUNCATE temp_events_staging;

\COPY temp_events_staging FROM '$event_file' WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');

-- Insert into events table with proper mapping
INSERT INTO events (
    game_id, inning, batting_team_id, home_away, outs, balls, strikes, pitch_sequence,
    away_score, home_score, batter_id, batter_hand, responsible_batter_id, responsible_batter_hand,
    pitcher_id, pitcher_hand, responsible_pitcher_id, responsible_pitcher_hand,
    fielder_2_id, fielder_3_id, fielder_4_id, fielder_5_id, fielder_6_id,
    fielder_7_id, fielder_8_id, fielder_9_id,
    runner_1_id, runner_2_id, runner_3_id,
    event_text, leadoff_flag, pinch_hit_flag, batter_fielding_position, batter_lineup_position,
    event_code, ab_flag, hit_code, sacrifice_hit_flag, sacrifice_fly_flag, event_outs,
    double_play_flag, triple_play_flag, rbi, wild_pitch_flag, passed_ball_flag,
    fielding_code, batted_ball_code, bunt_flag, foul_flag, batted_ball_location,
    errors, error_1_fielder, error_1_type, error_2_fielder, error_2_type,
    error_3_fielder, error_3_type,
    batter_dest, runner_1_dest, runner_2_dest, runner_3_dest,
    runner_1_stolen_base, runner_2_stolen_base, runner_3_stolen_base,
    runner_1_caught_stealing, runner_2_caught_stealing, runner_3_caught_stealing,
    batter_play_text, runner_1_play_text, runner_2_play_text, runner_3_play_text,
    putout_1_fielder, putout_2_fielder, putout_3_fielder,
    assist_1_fielder, assist_2_fielder, assist_3_fielder, assist_4_fielder, assist_5_fielder,
    game_new_flag, game_end_flag
)
SELECT 
    NULLIF("GAME_ID", '') as "GAME_ID", 
    "INN_CT", 
    NULLIF("AWAY_TEAM_ID", '') as "AWAY_TEAM_ID",
    CASE WHEN "BAT_HOME_ID" = 0 THEN 'A' ELSE 'H' END,
    "OUTS_CT", "BALLS_CT", "STRIKES_CT", "PITCH_SEQ_TX",
    "AWAY_SCORE_CT", "HOME_SCORE_CT",
    NULLIF("BAT_ID", '') as "BAT_ID", 
    "BAT_HAND_CD", 
    NULLIF("RESP_BAT_ID", '') as "RESP_BAT_ID", 
    "RESP_BAT_HAND_CD",
    NULLIF("PIT_ID", '') as "PIT_ID", 
    "PIT_HAND_CD", 
    NULLIF("RESP_PIT_ID", '') as "RESP_PIT_ID", 
    "RESP_PIT_HAND_CD",
    NULLIF("POS2_FLD_ID", '') as "POS2_FLD_ID", 
    NULLIF("POS3_FLD_ID", '') as "POS3_FLD_ID", 
    NULLIF("POS4_FLD_ID", '') as "POS4_FLD_ID", 
    NULLIF("POS5_FLD_ID", '') as "POS5_FLD_ID", 
    NULLIF("POS6_FLD_ID", '') as "POS6_FLD_ID",
    NULLIF("POS7_FLD_ID", '') as "POS7_FLD_ID", 
    NULLIF("POS8_FLD_ID", '') as "POS8_FLD_ID", 
    NULLIF("POS9_FLD_ID", '') as "POS9_FLD_ID",
    NULLIF("BASE1_RUN_ID", '') as "BASE1_RUN_ID", 
    NULLIF("BASE2_RUN_ID", '') as "BASE2_RUN_ID", 
    NULLIF("BASE3_RUN_ID", '') as "BASE3_RUN_ID",
    "EVENT_TX", "LEADOFF_FL", "PH_FL", 
    CASE 
        WHEN "BAT_FLD_CD" ~ '^[0-9]+$' THEN "BAT_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "BAT_FLD_CD", 
    "BAT_LINEUP_ID",
    "EVENT_CD", "AB_FL", "H_CD", "SH_FL", "SF_FL", "EVENT_OUTS_CT",
    "DP_FL", "TP_FL", "RBI_CT", "WP_FL", "PB_FL",
    CASE 
        WHEN "FLD_CD" ~ '^[0-9]+$' THEN "FLD_CD"::INTEGER 
        ELSE NULL 
    END as "FLD_CD", 
    "BATTEDBALL_CD", "BUNT_FL", "FOUL_FL", "BATTEDBALL_LOC_TX",
    "ERR_CT", 
    CASE 
        WHEN "ERR1_FLD_CD" ~ '^[0-9]+$' THEN "ERR1_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "ERR1_FLD_CD", 
    CASE 
        WHEN "ERR1_CD" ~ '^[0-9]+$' THEN "ERR1_CD"::INTEGER 
        ELSE NULL 
    END as "ERR1_CD", 
    CASE 
        WHEN "ERR2_FLD_CD" ~ '^[0-9]+$' THEN "ERR2_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "ERR2_FLD_CD", 
    CASE 
        WHEN "ERR2_CD" ~ '^[0-9]+$' THEN "ERR2_CD"::INTEGER 
        ELSE NULL 
    END as "ERR2_CD",
    CASE 
        WHEN "ERR3_FLD_CD" ~ '^[0-9]+$' THEN "ERR3_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "ERR3_FLD_CD", 
    CASE 
        WHEN "ERR3_CD" ~ '^[0-9]+$' THEN "ERR3_CD"::INTEGER 
        ELSE NULL 
    END as "ERR3_CD",
    "BAT_DEST_ID", "RUN1_DEST_ID", "RUN2_DEST_ID", "RUN3_DEST_ID",
    "RUN1_SB_FL", "RUN2_SB_FL", "RUN3_SB_FL",
    "RUN1_CS_FL", "RUN2_CS_FL", "RUN3_CS_FL",
    "BAT_PLAY_TX", "RUN1_PLAY_TX", "RUN2_PLAY_TX", "RUN3_PLAY_TX",
    CASE 
        WHEN "PO1_FLD_CD" ~ '^[0-9]+$' THEN "PO1_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "PO1_FLD_CD", 
    CASE 
        WHEN "PO2_FLD_CD" ~ '^[0-9]+$' THEN "PO2_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "PO2_FLD_CD", 
    CASE 
        WHEN "PO3_FLD_CD" ~ '^[0-9]+$' THEN "PO3_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "PO3_FLD_CD",
    CASE 
        WHEN "ASS1_FLD_CD" ~ '^[0-9]+$' THEN "ASS1_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "ASS1_FLD_CD", 
    CASE 
        WHEN "ASS2_FLD_CD" ~ '^[0-9]+$' THEN "ASS2_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "ASS2_FLD_CD", 
    CASE 
        WHEN "ASS3_FLD_CD" ~ '^[0-9]+$' THEN "ASS3_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "ASS3_FLD_CD", 
    CASE 
        WHEN "ASS4_FLD_CD" ~ '^[0-9]+$' THEN "ASS4_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "ASS4_FLD_CD", 
    CASE 
        WHEN "ASS5_FLD_CD" ~ '^[0-9]+$' THEN "ASS5_FLD_CD"::INTEGER 
        ELSE NULL 
    END as "ASS5_FLD_CD",
    "GAME_NEW_FL", "GAME_END_FL"
FROM temp_events_staging
WHERE "GAME_ID" IS NOT NULL;

TRUNCATE temp_events_staging;
EOF
        
        echo "    ✓ Loaded $lines events for $year"
    fi
done

echo ""
echo "=========================================="
echo "Events Loading Complete!"
echo "=========================================="

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT 'Total Events: ' || COUNT(*) FROM events;
"

unset PGPASSWORD


