-- Baseball Stats Database Schema
-- Comprehensive schema for retrosheet data with optimized structure for stats queries

-- ============================================================================
-- REFERENCE TABLES
-- ============================================================================

-- Players table - core player information
CREATE TABLE IF NOT EXISTS players (
    player_id VARCHAR(10) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    batting_hand CHAR(1), -- L, R, S (switch)
    throwing_hand CHAR(1), -- L, R
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Franchises table: represents a franchise that can have multiple team instances
-- Example: Montreal Expos (MON) and Washington Nationals (WAS) are the same franchise
-- Example: Houston Astros moved from NL to AL but stayed the same franchise

CREATE TABLE IF NOT EXISTS franchises (
    franchise_id TEXT PRIMARY KEY,
    franchise_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teams table: represents a team instance (can be part of a franchise)
-- A franchise can have multiple teams (different cities, leagues, or time periods)
-- Example: MON (Montreal Expos 1969-2004) and WAS (Washington Nationals 2005-2021) share franchise_id
-- Example: HOU has two rows: NL (1962-2012) and AL (2013-2021), same franchise_id
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    franchise_id TEXT REFERENCES franchises(franchise_id),
    league TEXT,
    city TEXT,
    name TEXT,
    first_year INTEGER,
    last_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parks/Venues table
CREATE TABLE IF NOT EXISTS parks (
    park_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(2),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Umpires table
CREATE TABLE IF NOT EXISTS umpires (
    umpire_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- GAME TABLES
-- ============================================================================

-- Games table - comprehensive game information
CREATE TABLE IF NOT EXISTS games (
    game_id VARCHAR(20) PRIMARY KEY,
    game_date DATE NOT NULL,
    season INTEGER,
    game_number INTEGER DEFAULT 0,
    day_of_week VARCHAR(10),
    start_time VARCHAR(10),
    daynight CHAR(1), -- D (day), N (night)
    dh_flag CHAR(1), -- T (true), F (false)
    
    -- Teams
    home_team_id VARCHAR(5) REFERENCES teams(team_id),
    away_team_id VARCHAR(5) REFERENCES teams(team_id),
    
    -- Venue
    park_id VARCHAR(10) REFERENCES parks(park_id),
    
    -- Scores
    home_score INTEGER,
    away_score INTEGER,
    home_hits INTEGER,
    away_hits INTEGER,
    home_errors INTEGER,
    away_errors INTEGER,
    home_lob INTEGER, -- Left on base
    away_lob INTEGER,
    
    -- Game details
    innings INTEGER,
    minutes INTEGER,
    attendance INTEGER,
    
    -- Weather
    temperature INTEGER,
    wind_direction VARCHAR(10),
    wind_speed INTEGER,
    field_condition VARCHAR(20),
    precipitation VARCHAR(20),
    sky VARCHAR(20),
    
    -- Pitchers of record
    winning_pitcher_id VARCHAR(10) REFERENCES players(player_id),
    losing_pitcher_id VARCHAR(10) REFERENCES players(player_id),
    save_pitcher_id VARCHAR(10) REFERENCES players(player_id),
    game_winning_rbi_id VARCHAR(10) REFERENCES players(player_id),
    
    -- Starting pitchers
    home_start_pitcher_id VARCHAR(10) REFERENCES players(player_id),
    away_start_pitcher_id VARCHAR(10) REFERENCES players(player_id),
    home_finish_pitcher_id VARCHAR(10) REFERENCES players(player_id),
    away_finish_pitcher_id VARCHAR(10) REFERENCES players(player_id),
    
    -- Umpires
    home_plate_umpire_id VARCHAR(10) REFERENCES umpires(umpire_id),
    first_base_umpire_id VARCHAR(10) REFERENCES umpires(umpire_id),
    second_base_umpire_id VARCHAR(10) REFERENCES umpires(umpire_id),
    third_base_umpire_id VARCHAR(10) REFERENCES umpires(umpire_id),
    left_field_umpire_id VARCHAR(10) REFERENCES umpires(umpire_id),
    right_field_umpire_id VARCHAR(10) REFERENCES umpires(umpire_id),
    
    -- Game type
    game_type VARCHAR(20) DEFAULT 'regular', -- regular, playoff, world_series, etc.
    forfeit_flag CHAR(1),
    suspend_flag CHAR(1),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game lineups - starting lineups for each game
CREATE TABLE IF NOT EXISTS game_lineups (
    game_id VARCHAR(20) REFERENCES games(game_id),
    team_id VARCHAR(5) REFERENCES teams(team_id),
    home_away CHAR(1), -- H (home), A (away)
    lineup_position INTEGER, -- 1-9
    player_id VARCHAR(10) REFERENCES players(player_id),
    fielding_position INTEGER, -- 1-9 (1=P, 2=C, 3=1B, 4=2B, 5=3B, 6=SS, 7=LF, 8=CF, 9=RF)
    PRIMARY KEY (game_id, team_id, lineup_position)
);

-- ============================================================================
-- EVENT TABLES (Play-by-Play)
-- ============================================================================

-- Events table - play-by-play events
CREATE TABLE IF NOT EXISTS events (
    event_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) REFERENCES games(game_id),
    inning INTEGER NOT NULL,
    batting_team_id VARCHAR(5) REFERENCES teams(team_id),
    home_away CHAR(1), -- 0 (away), 1 (home)
    
    -- Count
    outs INTEGER,
    balls INTEGER,
    strikes INTEGER,
    pitch_sequence TEXT,
    
    -- Score
    away_score INTEGER,
    home_score INTEGER,
    
    -- Batter
    batter_id VARCHAR(10) REFERENCES players(player_id),
    batter_hand CHAR(1),
    responsible_batter_id VARCHAR(10) REFERENCES players(player_id),
    responsible_batter_hand CHAR(1),
    batter_lineup_position INTEGER,
    batter_fielding_position INTEGER,
    
    -- Pitcher
    pitcher_id VARCHAR(10) REFERENCES players(player_id),
    pitcher_hand CHAR(1),
    responsible_pitcher_id VARCHAR(10) REFERENCES players(player_id),
    responsible_pitcher_hand CHAR(1),
    
    -- Fielders
    fielder_2_id VARCHAR(10) REFERENCES players(player_id), -- Catcher
    fielder_3_id VARCHAR(10) REFERENCES players(player_id), -- First base
    fielder_4_id VARCHAR(10) REFERENCES players(player_id), -- Second base
    fielder_5_id VARCHAR(10) REFERENCES players(player_id), -- Third base
    fielder_6_id VARCHAR(10) REFERENCES players(player_id), -- Shortstop
    fielder_7_id VARCHAR(10) REFERENCES players(player_id), -- Left field
    fielder_8_id VARCHAR(10) REFERENCES players(player_id), -- Center field
    fielder_9_id VARCHAR(10) REFERENCES players(player_id), -- Right field
    
    -- Base runners
    runner_1_id VARCHAR(10) REFERENCES players(player_id),
    runner_2_id VARCHAR(10) REFERENCES players(player_id),
    runner_3_id VARCHAR(10) REFERENCES players(player_id),
    
    -- Event details
    event_text TEXT,
    event_code INTEGER,
    event_outs INTEGER,
    ab_flag CHAR(1), -- T (true), F (false)
    hit_code INTEGER, -- 0=none, 1=single, 2=double, 3=triple, 4=home run
    rbi INTEGER,
    
    -- Flags
    leadoff_flag CHAR(1),
    pinch_hit_flag CHAR(1),
    sacrifice_hit_flag CHAR(1),
    sacrifice_fly_flag CHAR(1),
    double_play_flag CHAR(1),
    triple_play_flag CHAR(1),
    wild_pitch_flag CHAR(1),
    passed_ball_flag CHAR(1),
    bunt_flag CHAR(1),
    foul_flag CHAR(1),
    
    -- Batted ball
    batted_ball_code VARCHAR(10), -- F (fly), G (ground), L (line), P (pop)
    batted_ball_location TEXT,
    fielding_code INTEGER,
    
    -- Errors
    errors INTEGER,
    error_1_fielder INTEGER,
    error_1_type INTEGER,
    error_2_fielder INTEGER,
    error_2_type INTEGER,
    error_3_fielder INTEGER,
    error_3_type INTEGER,
    
    -- Base running
    batter_dest INTEGER, -- 0=out, 1=1B, 2=2B, 3=3B, 4=home
    runner_1_dest INTEGER,
    runner_2_dest INTEGER,
    runner_3_dest INTEGER,
    runner_1_stolen_base CHAR(1),
    runner_2_stolen_base CHAR(1),
    runner_3_stolen_base CHAR(1),
    runner_1_caught_stealing CHAR(1),
    runner_2_caught_stealing CHAR(1),
    runner_3_caught_stealing CHAR(1),
    
    -- Play details
    batter_play_text TEXT,
    runner_1_play_text TEXT,
    runner_2_play_text TEXT,
    runner_3_play_text TEXT,
    
    -- Putouts and assists
    putout_1_fielder INTEGER,
    putout_2_fielder INTEGER,
    putout_3_fielder INTEGER,
    assist_1_fielder INTEGER,
    assist_2_fielder INTEGER,
    assist_3_fielder INTEGER,
    assist_4_fielder INTEGER,
    assist_5_fielder INTEGER,
    
    -- Game state flags
    game_new_flag CHAR(1),
    game_end_flag CHAR(1),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- STATISTICS TABLES (Game-level stats)
-- ============================================================================

-- Batting stats per game
CREATE TABLE IF NOT EXISTS batting_stats (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) REFERENCES games(game_id),
    player_id VARCHAR(10) REFERENCES players(player_id),
    team_id VARCHAR(5) REFERENCES teams(team_id),
    season INTEGER,
    game_date DATE,
    
    -- Plate appearances
    plate_appearances INTEGER DEFAULT 0,
    at_bats INTEGER DEFAULT 0,
    
    -- Hits
    hits INTEGER DEFAULT 0,
    singles INTEGER DEFAULT 0,
    doubles INTEGER DEFAULT 0,
    triples INTEGER DEFAULT 0,
    home_runs INTEGER DEFAULT 0,
    
    -- Runs and RBIs
    runs INTEGER DEFAULT 0,
    rbis INTEGER DEFAULT 0,
    
    -- Walks and strikeouts
    walks INTEGER DEFAULT 0,
    intentional_walks INTEGER DEFAULT 0,
    strikeouts INTEGER DEFAULT 0,
    hit_by_pitch INTEGER DEFAULT 0,
    
    -- Other
    sacrifice_hits INTEGER DEFAULT 0,
    sacrifice_flies INTEGER DEFAULT 0,
    stolen_bases INTEGER DEFAULT 0,
    caught_stealing INTEGER DEFAULT 0,
    grounded_into_double_play INTEGER DEFAULT 0,
    reached_on_error INTEGER DEFAULT 0,
    
    -- Calculated fields (can be computed, but stored for performance)
    batting_average DECIMAL(5,3), -- hits / at_bats
    on_base_percentage DECIMAL(5,3), -- (hits + walks + hbp) / (ab + walks + hbp + sf)
    slugging_percentage DECIMAL(5,3), -- (singles + 2*doubles + 3*triples + 4*hr) / ab
    ops DECIMAL(5,3), -- obp + slg
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, player_id, team_id)
);

-- Pitching stats per game
CREATE TABLE IF NOT EXISTS pitching_stats (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) REFERENCES games(game_id),
    player_id VARCHAR(10) REFERENCES players(player_id),
    team_id VARCHAR(5) REFERENCES teams(team_id),
    season INTEGER,
    game_date DATE,
    
    -- Outs and innings
    outs_pitched INTEGER DEFAULT 0, -- outs recorded (3 per inning)
    innings_pitched DECIMAL(4,1), -- calculated from outs_pitched / 3
    batters_faced INTEGER DEFAULT 0,
    
    -- Hits allowed
    hits_allowed INTEGER DEFAULT 0,
    doubles_allowed INTEGER DEFAULT 0,
    triples_allowed INTEGER DEFAULT 0,
    home_runs_allowed INTEGER DEFAULT 0,
    
    -- Runs
    runs_allowed INTEGER DEFAULT 0,
    earned_runs INTEGER DEFAULT 0,
    
    -- Walks and strikeouts
    walks_allowed INTEGER DEFAULT 0,
    intentional_walks INTEGER DEFAULT 0,
    strikeouts INTEGER DEFAULT 0,
    hit_batters INTEGER DEFAULT 0,
    
    -- Other
    wild_pitches INTEGER DEFAULT 0,
    balks INTEGER DEFAULT 0,
    sacrifice_hits_allowed INTEGER DEFAULT 0,
    sacrifice_flies_allowed INTEGER DEFAULT 0,
    stolen_bases_allowed INTEGER DEFAULT 0,
    caught_stealing INTEGER DEFAULT 0,
    passed_balls INTEGER DEFAULT 0,
    
    -- Game outcomes
    win BOOLEAN DEFAULT FALSE,
    loss BOOLEAN DEFAULT FALSE,
    save BOOLEAN DEFAULT FALSE,
    game_started BOOLEAN DEFAULT FALSE,
    game_finished BOOLEAN DEFAULT FALSE,
    complete_game BOOLEAN DEFAULT FALSE,
    
    -- Calculated fields
    era DECIMAL(5,2), -- (earned_runs * 9) / innings_pitched
    whip DECIMAL(4,2), -- (walks + hits) / innings_pitched
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, player_id, team_id)
);

-- Fielding stats per game
CREATE TABLE IF NOT EXISTS fielding_stats (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) REFERENCES games(game_id),
    player_id VARCHAR(10) REFERENCES players(player_id),
    team_id VARCHAR(5) REFERENCES teams(team_id),
    position INTEGER, -- 1-9
    season INTEGER,
    game_date DATE,
    
    -- Fielding
    putouts INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    double_plays INTEGER DEFAULT 0,
    triple_plays INTEGER DEFAULT 0,
    passed_balls INTEGER DEFAULT 0,
    wild_pitches INTEGER DEFAULT 0,
    stolen_bases_allowed INTEGER DEFAULT 0,
    caught_stealing INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,
    
    -- Calculated fields
    fielding_percentage DECIMAL(5,3), -- (putouts + assists) / (putouts + assists + errors)
    chances INTEGER, -- putouts + assists + errors
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, player_id, team_id, position)
);

-- ============================================================================
-- ROSTER TABLES
-- ============================================================================

-- Rosters - player-team-season relationships
CREATE TABLE IF NOT EXISTS rosters (
    id BIGSERIAL PRIMARY KEY,
    player_id VARCHAR(10) REFERENCES players(player_id),
    team_id VARCHAR(5) REFERENCES teams(team_id),
    season INTEGER NOT NULL,
    position VARCHAR(10), -- Primary position
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, team_id, season)
);

-- Player seasons - aggregated player stats by season
CREATE TABLE IF NOT EXISTS player_seasons (
    id BIGSERIAL PRIMARY KEY,
    player_id VARCHAR(10) REFERENCES players(player_id),
    season INTEGER NOT NULL,
    team_id VARCHAR(5) REFERENCES teams(team_id),
    
    -- Games
    games INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,
    games_pitched INTEGER DEFAULT 0,
    games_started_pitcher INTEGER DEFAULT 0,
    games_relief INTEGER DEFAULT 0,
    
    -- Positions played
    games_catcher INTEGER DEFAULT 0,
    games_first_base INTEGER DEFAULT 0,
    games_second_base INTEGER DEFAULT 0,
    games_third_base INTEGER DEFAULT 0,
    games_shortstop INTEGER DEFAULT 0,
    games_left_field INTEGER DEFAULT 0,
    games_center_field INTEGER DEFAULT 0,
    games_right_field INTEGER DEFAULT 0,
    games_outfield INTEGER DEFAULT 0,
    games_designated_hitter INTEGER DEFAULT 0,
    games_pinch_hitter INTEGER DEFAULT 0,
    games_pinch_runner INTEGER DEFAULT 0,
    
    first_game_date DATE,
    last_game_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season, team_id)
);

-- ============================================================================
-- TEAM STATS TABLES
-- ============================================================================

-- Team game stats - per-game team statistics
CREATE TABLE IF NOT EXISTS team_game_stats (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) REFERENCES games(game_id),
    team_id VARCHAR(5) REFERENCES teams(team_id),
    home_away CHAR(1), -- H (home), A (away)
    season INTEGER,
    game_date DATE,
    
    -- Inning scores (can store up to 30 innings if needed)
    inn1 INTEGER, inn2 INTEGER, inn3 INTEGER, inn4 INTEGER, inn5 INTEGER,
    inn6 INTEGER, inn7 INTEGER, inn8 INTEGER, inn9 INTEGER,
    inn10 INTEGER, inn11 INTEGER, inn12 INTEGER, inn13 INTEGER, inn14 INTEGER, inn15 INTEGER,
    inn16 INTEGER, inn17 INTEGER, inn18 INTEGER, inn19 INTEGER, inn20 INTEGER,
    inn21 INTEGER, inn22 INTEGER, inn23 INTEGER, inn24 INTEGER, inn25 INTEGER,
    inn26 INTEGER, inn27 INTEGER, inn28 INTEGER,
    
    -- Team batting stats
    team_pa INTEGER DEFAULT 0,
    team_ab INTEGER DEFAULT 0,
    team_r INTEGER DEFAULT 0,
    team_h INTEGER DEFAULT 0,
    team_d INTEGER DEFAULT 0,
    team_t INTEGER DEFAULT 0,
    team_hr INTEGER DEFAULT 0,
    team_rbi INTEGER DEFAULT 0,
    team_sh INTEGER DEFAULT 0,
    team_sf INTEGER DEFAULT 0,
    team_hbp INTEGER DEFAULT 0,
    team_w INTEGER DEFAULT 0,
    team_iw INTEGER DEFAULT 0,
    team_k INTEGER DEFAULT 0,
    team_sb INTEGER DEFAULT 0,
    team_cs INTEGER DEFAULT 0,
    team_gdp INTEGER DEFAULT 0,
    team_lob INTEGER DEFAULT 0,
    
    -- Team pitching stats
    team_ipouts INTEGER DEFAULT 0,
    team_bfp INTEGER DEFAULT 0,
    team_p_h INTEGER DEFAULT 0,
    team_p_d INTEGER DEFAULT 0,
    team_p_t INTEGER DEFAULT 0,
    team_p_hr INTEGER DEFAULT 0,
    team_p_r INTEGER DEFAULT 0,
    team_p_er INTEGER DEFAULT 0,
    team_p_w INTEGER DEFAULT 0,
    team_p_iw INTEGER DEFAULT 0,
    team_p_k INTEGER DEFAULT 0,
    team_p_hbp INTEGER DEFAULT 0,
    team_p_wp INTEGER DEFAULT 0,
    team_p_bk INTEGER DEFAULT 0,
    
    -- Team fielding stats
    team_po INTEGER DEFAULT 0,
    team_a INTEGER DEFAULT 0,
    team_e INTEGER DEFAULT 0,
    team_dp INTEGER DEFAULT 0,
    team_tp INTEGER DEFAULT 0,
    
    -- Game outcome
    win BOOLEAN DEFAULT FALSE,
    loss BOOLEAN DEFAULT FALSE,
    tie BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, team_id)
);

-- ============================================================================
-- INDEXES for Performance
-- ============================================================================

-- Games indexes
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);
CREATE INDEX IF NOT EXISTS idx_games_home_team ON games(home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away_team ON games(away_team_id);
CREATE INDEX IF NOT EXISTS idx_games_park ON games(park_id);

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_game ON events(game_id);
CREATE INDEX IF NOT EXISTS idx_events_batter ON events(batter_id);
CREATE INDEX IF NOT EXISTS idx_events_pitcher ON events(pitcher_id);
CREATE INDEX IF NOT EXISTS idx_events_game_inning ON events(game_id, inning);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(game_id) INCLUDE (inning);

-- Batting stats indexes
CREATE INDEX IF NOT EXISTS idx_batting_player ON batting_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_batting_team ON batting_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_batting_season ON batting_stats(season);
CREATE INDEX IF NOT EXISTS idx_batting_game ON batting_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_batting_date ON batting_stats(game_date);

-- Pitching stats indexes
CREATE INDEX IF NOT EXISTS idx_pitching_player ON pitching_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_pitching_team ON pitching_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_pitching_season ON pitching_stats(season);
CREATE INDEX IF NOT EXISTS idx_pitching_game ON pitching_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_pitching_date ON pitching_stats(game_date);

-- Fielding stats indexes
CREATE INDEX IF NOT EXISTS idx_fielding_player ON fielding_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_fielding_team ON fielding_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_fielding_season ON fielding_stats(season);
CREATE INDEX IF NOT EXISTS idx_fielding_position ON fielding_stats(position);
CREATE INDEX IF NOT EXISTS idx_fielding_game ON fielding_stats(game_id);

-- Roster indexes
CREATE INDEX IF NOT EXISTS idx_rosters_player ON rosters(player_id);
CREATE INDEX IF NOT EXISTS idx_rosters_team ON rosters(team_id);
CREATE INDEX IF NOT EXISTS idx_rosters_season ON rosters(season);

-- Player seasons indexes
CREATE INDEX IF NOT EXISTS idx_player_seasons_player ON player_seasons(player_id);
CREATE INDEX IF NOT EXISTS idx_player_seasons_season ON player_seasons(season);
CREATE INDEX IF NOT EXISTS idx_player_seasons_team ON player_seasons(team_id);

-- Team game stats indexes
CREATE INDEX IF NOT EXISTS idx_team_game_stats_team ON team_game_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_season ON team_game_stats(season);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_date ON team_game_stats(game_date);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_game ON team_game_stats(game_id);

-- ============================================================================
-- VIEWS for Common Queries
-- ============================================================================

-- View: Career batting stats by player
CREATE OR REPLACE VIEW v_player_career_batting AS
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
LEFT JOIN batting_stats bs ON p.player_id = bs.player_id
GROUP BY p.player_id, p.first_name, p.last_name;

-- View: Career pitching stats by player
CREATE OR REPLACE VIEW v_player_career_pitching AS
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
LEFT JOIN pitching_stats ps ON p.player_id = ps.player_id
GROUP BY p.player_id, p.first_name, p.last_name;

-- View: Season batting leaders
CREATE OR REPLACE VIEW v_season_batting_leaders AS
SELECT 
    season,
    player_id,
    (SELECT first_name || ' ' || last_name FROM players WHERE player_id = bs.player_id) as player_name,
    SUM(at_bats) as ab,
    SUM(hits) as h,
    SUM(home_runs) as hr,
    SUM(rbis) as rbi,
    SUM(runs) as r,
    CASE WHEN SUM(at_bats) > 0 
         THEN ROUND(SUM(hits)::DECIMAL / SUM(at_bats), 3) 
         ELSE 0 END as avg,
    CASE WHEN (SUM(at_bats) + SUM(walks) + SUM(hit_by_pitch) + SUM(sacrifice_flies)) > 0
         THEN ROUND((SUM(hits) + SUM(walks) + SUM(hit_by_pitch))::DECIMAL / 
                    (SUM(at_bats) + SUM(walks) + SUM(hit_by_pitch) + SUM(sacrifice_flies)), 3)
         ELSE 0 END as obp,
    CASE WHEN SUM(at_bats) > 0
         THEN ROUND((SUM(singles) + 2*SUM(doubles) + 3*SUM(triples) + 4*SUM(home_runs))::DECIMAL / SUM(at_bats), 3)
         ELSE 0 END as slg
FROM batting_stats bs
WHERE at_bats >= 502 -- Qualified (3.1 PA per team game, ~502 for 162 game season)
GROUP BY season, player_id
ORDER BY season DESC, avg DESC;

-- View: Season pitching leaders
CREATE OR REPLACE VIEW v_season_pitching_leaders AS
SELECT 
    season,
    player_id,
    (SELECT first_name || ' ' || last_name FROM players WHERE player_id = ps.player_id) as player_name,
    SUM(innings_pitched) as ip,
    SUM(hits_allowed) as h,
    SUM(home_runs_allowed) as hr,
    SUM(runs_allowed) as r,
    SUM(earned_runs) as er,
    SUM(walks_allowed) as w,
    SUM(strikeouts) as k,
    SUM(win::INTEGER) as wins,
    SUM(loss::INTEGER) as losses,
    CASE WHEN SUM(innings_pitched) > 0
         THEN ROUND((SUM(earned_runs) * 9.0) / SUM(innings_pitched), 2)
         ELSE 0 END as era,
    CASE WHEN SUM(innings_pitched) > 0
         THEN ROUND((SUM(walks_allowed) + SUM(hits_allowed))::DECIMAL / SUM(innings_pitched), 2)
         ELSE 0 END as whip
FROM pitching_stats ps
WHERE innings_pitched >= 162 -- Qualified (1 IP per team game, ~162 for 162 game season)
GROUP BY season, player_id
ORDER BY season DESC, era ASC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE games IS 'Comprehensive game information from retrosheet';
COMMENT ON TABLE events IS 'Play-by-play event data for each game';
COMMENT ON TABLE batting_stats IS 'Game-level batting statistics';
COMMENT ON TABLE pitching_stats IS 'Game-level pitching statistics';
COMMENT ON TABLE fielding_stats IS 'Game-level fielding statistics';
COMMENT ON TABLE rosters IS 'Player-team-season roster information';
COMMENT ON VIEW v_player_career_batting IS 'Career batting statistics aggregated by player';
COMMENT ON VIEW v_player_career_pitching IS 'Career pitching statistics aggregated by player';

