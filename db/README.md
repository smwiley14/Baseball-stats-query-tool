# Baseball Stats Database Schema

This directory contains the database schema for storing and querying retrosheet baseball data.

## Files

- `schema.sql` - Complete database schema with tables, indexes, and views
- `init.sql` - Original simple schema (legacy)
- `README.md` - This file

## Schema Overview

The schema is designed for efficient querying of baseball statistics with the following main components:

### Core Tables

1. **Reference Tables**
   - `players` - Player information (name, batting/throwing hand)
   - `teams` - Team information (league, city, name)
   - `parks` - Ballpark/venue information
   - `umpires` - Umpire information

2. **Game Tables**
   - `games` - Comprehensive game information (scores, weather, umpires, etc.)
   - `game_lineups` - Starting lineups for each game

3. **Event Tables**
   - `events` - Play-by-play event data (every pitch, at-bat, etc.)

4. **Statistics Tables**
   - `batting_stats` - Game-level batting statistics
   - `pitching_stats` - Game-level pitching statistics
   - `fielding_stats` - Game-level fielding statistics
   - `team_game_stats` - Team-level statistics per game

5. **Roster Tables**
   - `rosters` - Player-team-season relationships
   - `player_seasons` - Aggregated player stats by season

### Views

- `v_player_career_batting` - Career batting stats by player
- `v_player_career_pitching` - Career pitching stats by player
- `v_season_batting_leaders` - Season batting leaders (qualified)
- `v_season_pitching_leaders` - Season pitching leaders (qualified)

## Example Queries

### Player Career Stats

```sql
-- Get career batting stats for a player
SELECT * FROM v_player_career_batting 
WHERE player_id = 'ruthb101'
ORDER BY last_season DESC;

-- Get career pitching stats for a player
SELECT * FROM v_player_career_pitching 
WHERE player_id = 'johnw101'
ORDER BY last_season DESC;
```

### Season Leaders

```sql
-- Top 10 batting average leaders for 2020
SELECT player_name, ab, h, hr, rbi, avg, obp, slg, 
       ROUND(obp + slg, 3) as ops
FROM v_season_batting_leaders
WHERE season = 2020
ORDER BY avg DESC
LIMIT 10;

-- Top 10 ERA leaders for 2020 (qualified)
SELECT player_name, ip, h, hr, w, k, wins, losses, era, whip
FROM v_season_pitching_leaders
WHERE season = 2020
ORDER BY era ASC
LIMIT 10;
```

### Game-by-Game Stats

```sql
-- Get all games for a team in a season
SELECT g.game_id, g.game_date, 
       t1.name as home_team, t2.name as away_team,
       g.home_score, g.away_score,
       g.attendance, g.park_id
FROM games g
JOIN teams t1 ON g.home_team_id = t1.team_id
JOIN teams t2 ON g.away_team_id = t2.team_id
WHERE g.season = 2020 
  AND (g.home_team_id = 'NYY' OR g.away_team_id = 'NYY')
ORDER BY g.game_date;

-- Get a player's game-by-game stats for a season
SELECT bs.game_date, 
       t.name as opponent,
       bs.at_bats, bs.hits, bs.home_runs, bs.rbis, bs.runs,
       bs.walks, bs.strikeouts
FROM batting_stats bs
JOIN games g ON bs.game_id = g.game_id
JOIN teams t ON (CASE WHEN g.home_team_id = bs.team_id 
                      THEN g.away_team_id 
                      ELSE g.home_team_id END) = t.team_id
WHERE bs.player_id = 'judga001' 
  AND bs.season = 2020
ORDER BY bs.game_date;
```

### Team Stats

```sql
-- Team record for a season
SELECT 
    t.name as team,
    COUNT(*) FILTER (WHERE tgs.win = TRUE) as wins,
    COUNT(*) FILTER (WHERE tgs.loss = TRUE) as losses,
    COUNT(*) FILTER (WHERE tgs.tie = TRUE) as ties,
    ROUND(COUNT(*) FILTER (WHERE tgs.win = TRUE)::DECIMAL / 
          NULLIF(COUNT(*) FILTER (WHERE tgs.win = TRUE) + 
                 COUNT(*) FILTER (WHERE tgs.loss = TRUE), 0), 3) as win_pct,
    SUM(tgs.team_r) as runs_scored,
    SUM(tgs.team_p_r) as runs_allowed
FROM team_game_stats tgs
JOIN teams t ON tgs.team_id = t.team_id
WHERE tgs.season = 2020
GROUP BY t.team_id, t.name
ORDER BY win_pct DESC;
```

### Play-by-Play Analysis

```sql
-- Get all events for a specific game
SELECT e.inning, e.outs, e.batter_id, e.pitcher_id,
       e.event_text, e.hit_code, e.rbi,
       p1.last_name as batter_name,
       p2.last_name as pitcher_name
FROM events e
LEFT JOIN players p1 ON e.batter_id = p1.player_id
LEFT JOIN players p2 ON e.pitcher_id = p2.player_id
WHERE e.game_id = 'NYY202007230'
ORDER BY e.inning, e.event_id;

-- Count home runs by player in a season
SELECT 
    p.first_name || ' ' || p.last_name as player_name,
    COUNT(*) as home_runs
FROM events e
JOIN players p ON e.batter_id = p.player_id
JOIN games g ON e.game_id = g.game_id
WHERE e.hit_code = 4  -- Home run
  AND g.season = 2020
GROUP BY p.player_id, p.first_name, p.last_name
ORDER BY home_runs DESC
LIMIT 20;
```

### Advanced Queries

```sql
-- Find players with highest OPS in a season (qualified)
SELECT 
    p.first_name || ' ' || p.last_name as player_name,
    t.name as team,
    SUM(bs.at_bats) as ab,
    SUM(bs.hits) as h,
    SUM(bs.home_runs) as hr,
    ROUND(SUM(bs.hits)::DECIMAL / SUM(bs.at_bats), 3) as avg,
    ROUND((SUM(bs.hits) + SUM(bs.walks) + SUM(bs.hit_by_pitch))::DECIMAL / 
          (SUM(bs.at_bats) + SUM(bs.walks) + SUM(bs.hit_by_pitch) + SUM(bs.sacrifice_flies)), 3) as obp,
    ROUND((SUM(bs.singles) + 2*SUM(bs.doubles) + 3*SUM(bs.triples) + 4*SUM(bs.home_runs))::DECIMAL / 
          SUM(bs.at_bats), 3) as slg,
    ROUND((SUM(bs.hits) + SUM(bs.walks) + SUM(bs.hit_by_pitch))::DECIMAL / 
          (SUM(bs.at_bats) + SUM(bs.walks) + SUM(bs.hit_by_pitch) + SUM(bs.sacrifice_flies)) +
          (SUM(bs.singles) + 2*SUM(bs.doubles) + 3*SUM(bs.triples) + 4*SUM(bs.home_runs))::DECIMAL / 
          SUM(bs.at_bats), 3) as ops
FROM batting_stats bs
JOIN players p ON bs.player_id = p.player_id
JOIN teams t ON bs.team_id = t.team_id
WHERE bs.season = 2020
  AND bs.at_bats >= 502  -- Qualified
GROUP BY p.player_id, p.first_name, p.last_name, t.name
ORDER BY ops DESC
LIMIT 20;

-- Pitcher vs Batter matchups
SELECT 
    p1.last_name as batter_name,
    p2.last_name as pitcher_name,
    COUNT(*) as at_bats,
    SUM(CASE WHEN e.hit_code > 0 THEN 1 ELSE 0 END) as hits,
    SUM(CASE WHEN e.hit_code = 4 THEN 1 ELSE 0 END) as home_runs,
    ROUND(SUM(CASE WHEN e.hit_code > 0 THEN 1 ELSE 0 END)::DECIMAL / COUNT(*), 3) as avg
FROM events e
JOIN players p1 ON e.batter_id = p1.player_id
JOIN players p2 ON e.pitcher_id = p2.player_id
WHERE e.ab_flag = 'T'
  AND e.batter_id = 'judga001'
GROUP BY p1.player_id, p1.last_name, p2.player_id, p2.last_name
HAVING COUNT(*) >= 10  -- At least 10 at-bats
ORDER BY avg DESC;
```

## Data Loading

The schema is designed to work with the CSV files generated by the processing scripts:

1. **Reference Data**: Load from `data/processed/rosters/*.csv` and team files
2. **Games**: Load from `data/processed/games/*.csv` or `data/gameinfo.csv`
3. **Events**: Load from `data/processed/events/*.csv`
4. **Stats**: Load from `data/batting.csv`, `data/pitching.csv`, `data/fielding.csv`
5. **Team Stats**: Load from `data/teamstats.csv`

## Performance Considerations

- All foreign key columns are indexed
- Date and season columns are indexed for time-based queries
- Views pre-aggregate common statistics for faster queries
- Consider partitioning large tables (events, batting_stats) by season for very large datasets

## Notes

- The schema uses PostgreSQL-specific features (SERIAL, BIGSERIAL, BOOLEAN)
- For other databases, you may need to adjust data types
- Some fields allow NULL values for historical data completeness
- Calculated fields (AVG, OBP, SLG, ERA, WHIP) can be computed on-the-fly or stored for performance


