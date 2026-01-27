# Loading Data into the Database

This guide explains how to load all CSV data into the PostgreSQL database.

## Prerequisites

1. PostgreSQL database is running (via docker-compose or standalone)
2. Database schema has been created (`schema.sql`)
3. CSV files are available in the `data/` directory

## Quick Start

### 1. Create the Schema

First, create all tables, indexes, and views:

```bash
psql -h localhost -p 5433 -U baseball -d retrosheet -f db/schema.sql
```

Or using docker:

```bash
docker exec -i retrosheet-postgres psql -U baseball -d retrosheet < db/schema.sql
```

### 2. Load All Data

Run the main loading script:

```bash
./db/load_data.sh
```

This script will:
1. Load players from roster files
2. Load teams
3. Load games from `gameinfo.csv`
4. Load rosters
5. Load batting stats from `batting.csv`
6. Load pitching stats from `pitching.csv`
7. Load fielding stats from `fielding.csv`
8. Update calculated fields (AVG, OBP, SLG, ERA, WHIP, etc.)

### 3. Load Events (Optional, Large Dataset)

Events can be very large. Load them separately:

```bash
./db/load_events.sh
```

## Environment Variables

You can customize the database connection:

```bash
export DB_HOST=localhost
export DB_PORT=5433
export DB_NAME=retrosheet
export DB_USER=baseball
export DB_PASSWORD=baseball

./db/load_data.sh
```

## Data Sources

The scripts load data from:

| Source | Table(s) | Description |
|--------|----------|-------------|
| `data/processed/rosters/*.csv` | `players`, `rosters` | Player info and rosters |
| `data/allplayers.csv` | `players`, `player_seasons` | Additional player data |
| `data/gameinfo.csv` | `games` | Game information |
| `data/processed/games/*.csv` | `games` | Detailed game data (if available) |
| `data/batting.csv` | `batting_stats` | Batting statistics |
| `data/pitching.csv` | `pitching_stats` | Pitching statistics |
| `data/fielding.csv` | `fielding_stats` | Fielding statistics |
| `data/processed/events/*.csv` | `events` | Play-by-play events |
| `data/teamstats.csv` | `team_game_stats` | Team statistics (manual mapping needed) |

## Loading Order

Data must be loaded in this order due to foreign key constraints:

1. **Reference Tables**: `players`, `teams`, `parks`, `umpires`
2. **Games**: `games`, `game_lineups`
3. **Rosters**: `rosters`, `player_seasons`
4. **Statistics**: `batting_stats`, `pitching_stats`, `fielding_stats`
5. **Events**: `events` (can be loaded separately)
6. **Team Stats**: `team_game_stats`

## Manual Loading

If you prefer to load data manually or need custom transformations:

### Using psql COPY

```sql
-- Example: Load players
\COPY players(player_id, last_name, first_name, batting_hand, throwing_hand)
FROM 'data/processed/rosters/rosters_2020.csv'
WITH (FORMAT CSV, HEADER true, DELIMITER ',', NULL '');
```

### Using Python/Other Tools

You can also use Python with `psycopg2` or `pandas` + `sqlalchemy`:

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://baseball:baseball@localhost:5433/retrosheet')

# Load CSV
df = pd.read_csv('data/batting.csv')

# Transform if needed
df['season'] = pd.to_datetime(df['date']).dt.year

# Load to database
df.to_sql('batting_stats', engine, if_exists='append', index=False)
```

## Performance Tips

1. **Disable Indexes During Load**: Drop indexes before loading, recreate after
2. **Use COPY**: Much faster than INSERT statements
3. **Batch Processing**: Load year-by-year for very large datasets
4. **Parallel Loading**: Load different tables in parallel if possible
5. **Vacuum After Loading**: Run `VACUUM ANALYZE` after loading

Example:

```sql
-- Before loading
ALTER TABLE batting_stats DISABLE TRIGGER ALL;
DROP INDEX IF EXISTS idx_batting_player;
DROP INDEX IF EXISTS idx_batting_game;

-- Load data here...

-- After loading
CREATE INDEX idx_batting_player ON batting_stats(player_id);
CREATE INDEX idx_batting_game ON batting_stats(game_id);
ALTER TABLE batting_stats ENABLE TRIGGER ALL;
VACUUM ANALYZE batting_stats;
```

## Troubleshooting

### Foreign Key Violations

If you get foreign key violations, ensure:
- Players are loaded before rosters
- Teams are loaded before games
- Games are loaded before stats

### Missing Files

The script will skip missing files with a warning. Check that:
- CSV files exist in expected locations
- File paths are correct
- Files are readable

### Encoding Issues

If you encounter encoding issues:

```bash
# Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
```

### Large Files

For very large files (events), consider:
- Loading year-by-year
- Using `COPY` with `FORMAT CSV`
- Increasing `shared_buffers` and `work_mem` in PostgreSQL

## Verification

After loading, verify the data:

```sql
-- Check row counts
SELECT 
    'players' as table_name, COUNT(*) as rows FROM players
UNION ALL
SELECT 'teams', COUNT(*) FROM teams
UNION ALL
SELECT 'games', COUNT(*) FROM games
UNION ALL
SELECT 'batting_stats', COUNT(*) FROM batting_stats
UNION ALL
SELECT 'pitching_stats', COUNT(*) FROM pitching_stats
UNION ALL
SELECT 'fielding_stats', COUNT(*) FROM fielding_stats
UNION ALL
SELECT 'events', COUNT(*) FROM events;

-- Check for missing references
SELECT COUNT(*) as missing_players
FROM batting_stats bs
LEFT JOIN players p ON bs.player_id = p.player_id
WHERE p.player_id IS NULL;

-- Check date ranges
SELECT 
    MIN(game_date) as earliest_game,
    MAX(game_date) as latest_game,
    COUNT(DISTINCT season) as seasons
FROM games;
```

## Next Steps

After loading data:
1. Run `VACUUM ANALYZE` on all tables
2. Verify data integrity
3. Test queries using the views
4. Create additional indexes if needed for your query patterns

