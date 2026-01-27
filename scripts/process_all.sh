#!/bin/bash

# Master script to process all retrosheet data using chadwick tools
# This script orchestrates the processing of events, games, rosters, and box scores

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Retrosheet Data Processing Script"
echo "=========================================="
echo ""

# Check if chadwick tools are available
echo "Checking for chadwick tools..."
MISSING_TOOLS=()

if ! command -v cwevent &> /dev/null; then
    MISSING_TOOLS+=("cwevent")
fi

if ! command -v cwgame &> /dev/null; then
    MISSING_TOOLS+=("cwgame")
fi

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo "ERROR: Missing required chadwick tools: ${MISSING_TOOLS[*]}"
    echo ""
    echo "Please install chadwick tools:"
    echo "  macOS: brew install chadwick"
    echo "  Linux: Download from https://github.com/chadwickbureau/chadwick"
    echo "  Or build from source: https://github.com/chadwickbureau/chadwick"
    exit 1
fi

echo "✓ All required chadwick tools found"
echo "  Note: Roster files are processed directly (no cwroster tool needed)"
echo ""

# Organize source directories (move *seve to data/events, *box to data/box_scores)
echo "Organizing source directories..."
if [ -f "parse.sh" ]; then
    # Only move directories if they're not already organized
    if [ ! -d "data/events" ] || [ -z "$(ls -A data/events 2>/dev/null)" ]; then
        echo "  Moving event directories to data/events/"
        mkdir -p data/events
        for dir in data/*seve; do
            if [ -d "$dir" ]; then
                mv "$dir" data/events/ 2>/dev/null || true
            fi
        done
    fi
    
    if [ ! -d "data/box_scores" ] || [ -z "$(ls -A data/box_scores 2>/dev/null)" ]; then
        echo "  Moving box score directories to data/box_scores/"
        mkdir -p data/box_scores
        for dir in data/*box; do
            if [ -d "$dir" ]; then
                mv "$dir" data/box_scores/ 2>/dev/null || true
            fi
        done
    fi
    echo "  Directory organization complete"
    echo ""
fi

# Create output directories
mkdir -p data/processed/events
mkdir -p data/processed/games
mkdir -p data/processed/rosters
mkdir -p data/processed/box_scores
mkdir -p data/combined

# Process events
echo "=========================================="
echo "Step 1: Processing Event Files"
echo "=========================================="
bash "$SCRIPT_DIR/process_events.sh"
echo ""

# Process games
echo "=========================================="
echo "Step 2: Processing Game Files"
echo "=========================================="
bash "$SCRIPT_DIR/process_games.sh"
echo ""

# Process rosters
echo "=========================================="
echo "Step 3: Processing Roster Files"
echo "=========================================="
bash "$SCRIPT_DIR/process_rosters.sh"
echo ""

# Process box scores (optional, may not be available)
echo "=========================================="
echo "Step 4: Processing Box Score Files"
echo "=========================================="
bash "$SCRIPT_DIR/process_box_scores.sh"
echo ""

# Combine outputs
echo "=========================================="
echo "Step 5: Combining Output Files"
echo "=========================================="
bash "$SCRIPT_DIR/combine_outputs.sh"
echo ""

echo "=========================================="
echo "Processing Complete!"
echo "=========================================="
echo ""
echo "Output files are in:"
echo "  - Individual files: data/processed/"
echo "  - Combined files: data/combined/"
echo ""
echo "Summary:"
if [ -d "data/processed/events" ]; then
    event_count=$(find data/processed/events -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')
    echo "  - Event files: $event_count"
fi
if [ -d "data/processed/games" ]; then
    game_count=$(find data/processed/games -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')
    echo "  - Game files: $game_count"
fi
if [ -d "data/processed/rosters" ]; then
    roster_count=$(find data/processed/rosters -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')
    echo "  - Roster files: $roster_count"
fi
if [ -d "data/processed/box_scores" ]; then
    box_count=$(find data/processed/box_scores -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')
    echo "  - Box score files: $box_count"
fi
echo ""

