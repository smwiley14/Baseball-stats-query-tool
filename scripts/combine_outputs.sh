#!/bin/bash

# Script to combine all processed CSV files into single files
# This creates combined files for events, games, and rosters

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

PROCESSED_DIR="data/processed"
OUTPUT_DIR="data/combined"
mkdir -p "$OUTPUT_DIR"

echo "Combining processed files..."

# Combine event files
if [ -d "$PROCESSED_DIR/events" ]; then
    echo "Combining event files..."
    combined_events="$OUTPUT_DIR/all_events.csv"
    
    # Get header from first file
    first_file=$(ls -t "$PROCESSED_DIR/events"/*.csv 2>/dev/null | head -1)
    if [ -n "$first_file" ]; then
        # cwevent doesn't output headers by default, so we'll add our own
        # or use the first file as-is if it has headers
        head -1 "$first_file" > "$combined_events" 2>/dev/null || true
        
        # Combine all files (skip header if we added one)
        for file in "$PROCESSED_DIR/events"/*.csv; do
            if [ -f "$file" ] && [ -s "$file" ]; then
                if [ -s "$combined_events" ]; then
                    tail -n +2 "$file" >> "$combined_events" 2>/dev/null || cat "$file" >> "$combined_events"
                else
                    cat "$file" >> "$combined_events"
                fi
            fi
        done
        
        if [ -s "$combined_events" ]; then
            echo "  Created: $combined_events"
        fi
    fi
fi

# Combine game files
if [ -d "$PROCESSED_DIR/games" ]; then
    echo "Combining game files..."
    combined_games="$OUTPUT_DIR/all_games.csv"
    
    first_file=$(ls -t "$PROCESSED_DIR/games"/*.csv 2>/dev/null | head -1)
    if [ -n "$first_file" ]; then
        head -1 "$first_file" > "$combined_games" 2>/dev/null || true
        
        for file in "$PROCESSED_DIR/games"/*.csv; do
            if [ -f "$file" ] && [ -s "$file" ]; then
                if [ -s "$combined_games" ]; then
                    tail -n +2 "$file" >> "$combined_games" 2>/dev/null || cat "$file" >> "$combined_games"
                else
                    cat "$file" >> "$combined_games"
                fi
            fi
        done
        
        if [ -s "$combined_games" ]; then
            echo "  Created: $combined_games"
        fi
    fi
fi

# Combine roster files
if [ -d "$PROCESSED_DIR/rosters" ]; then
    echo "Combining roster files..."
    combined_rosters="$OUTPUT_DIR/all_rosters.csv"
    
    first_file=$(ls -t "$PROCESSED_DIR/rosters"/*.csv 2>/dev/null | head -1)
    if [ -n "$first_file" ]; then
        # Roster files have headers, so use the first file's header
        head -1 "$first_file" > "$combined_rosters" 2>/dev/null || true
        
        for file in "$PROCESSED_DIR/rosters"/*.csv; do
            if [ -f "$file" ] && [ -s "$file" ]; then
                if [ -s "$combined_rosters" ]; then
                    tail -n +2 "$file" >> "$combined_rosters" 2>/dev/null || cat "$file" >> "$combined_rosters"
                else
                    cat "$file" >> "$combined_rosters"
                fi
            fi
        done
        
        if [ -s "$combined_rosters" ]; then
            echo "  Created: $combined_rosters"
        fi
    fi
fi

# Combine box score files
if [ -d "$PROCESSED_DIR/box_scores" ]; then
    echo "Combining box score files..."
    combined_box="$OUTPUT_DIR/all_box_scores.csv"
    
    first_file=$(ls -t "$PROCESSED_DIR/box_scores"/*.csv 2>/dev/null | head -1)
    if [ -n "$first_file" ]; then
        head -1 "$first_file" > "$combined_box" 2>/dev/null || true
        
        for file in "$PROCESSED_DIR/box_scores"/*.csv; do
            if [ -f "$file" ] && [ -s "$file" ]; then
                if [ -s "$combined_box" ]; then
                    tail -n +2 "$file" >> "$combined_box" 2>/dev/null || cat "$file" >> "$combined_box"
                else
                    cat "$file" >> "$combined_box"
                fi
            fi
        done
        
        if [ -s "$combined_box" ]; then
            echo "  Created: $combined_box"
        fi
    fi
fi

echo "Combining complete!"

