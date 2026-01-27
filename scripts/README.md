# Retrosheet Data Processing Scripts

This directory contains scripts to process retrosheet data using chadwick tools.

## Prerequisites

You need to have chadwick tools installed:
- `cwevent` - for processing event files
- `cwgame` - for processing game files
- `cwbox` - for processing box score files (optional)

Note: Roster files (`.ROS`) are processed directly without chadwick tools, as they are already in CSV format.

### Installation

**macOS:**
```bash
brew install chadwick
```

**Linux:**
Download and build from source: https://github.com/chadwickbureau/chadwick

## Scripts

### `process_all.sh`
Master script that runs all processing steps. This is the main script you should run.

**Usage:**
```bash
./scripts/process_all.sh
```

### Individual Scripts

- **`process_events.sh`** - Processes all `.EVN` and `.EVA` files to extract play-by-play event data
- **`process_games.sh`** - Processes event files to extract game-level summaries
- **`process_rosters.sh`** - Processes all `.ROS` files to extract roster information (processes directly, no chadwick tool needed)
- **`process_box_scores.sh`** - Processes `.EBN` and `.EBA` files for box score data (optional)
- **`combine_outputs.sh`** - Combines all year-by-year CSV files into single combined files

## Output Structure

After running the scripts, you'll have:

```
data/
├── processed/
│   ├── events/          # Year-by-year event files (events_YYYY.csv)
│   ├── games/           # Year-by-year game files (games_YYYY.csv)
│   ├── rosters/         # Year-by-year roster files (rosters_YYYY.csv)
│   └── box_scores/      # Year-by-year box score files (box_scores_YYYY.csv)
└── combined/
    ├── all_events.csv   # Combined event data
    ├── all_games.csv    # Combined game data
    ├── all_rosters.csv  # Combined roster data
    └── all_box_scores.csv # Combined box score data
```

## Field Descriptions

### Events (cwevent)
The event files contain play-by-play data with fields 0-96. Common fields include:
- Game ID
- Inning
- Batting team
- Batter ID
- Event type
- Hit location
- And many more...

### Games (cwgame)
The game files contain game-level summaries with fields 0-83, including:
- Game ID
- Date
- Teams
- Score
- Attendance
- And more...

### Rosters
The roster files are already in CSV format and contain player information:
- `player_id` - Unique player identifier
- `last_name` - Player's last name
- `first_name` - Player's first name
- `batting_hand` - Batting hand (L/R)
- `throwing_hand` - Throwing hand (L/R)
- `team` - Team abbreviation
- `position` - Primary position

## Notes

- Scripts skip years that have already been processed (checks for existing output files)
- Empty output files are automatically removed
- Processing is done year-by-year to allow for incremental updates
- The scripts handle both event files (1910+) and box score files (pre-1910)

## Troubleshooting

If you encounter errors:
1. Verify chadwick tools are installed: `which cwevent cwgame`
2. Check that the data directory structure matches expected format
3. Ensure you have write permissions in the output directories
4. Check individual script outputs for specific error messages

