#!/bin/bash

# Script to process retrosheet game files using cwgame
# This processes all .EVN and .EVA files to extract game-level data

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

SRC_DIR="data/events"
OUTPUT_DIR="data/processed/games"
mkdir -p "$OUTPUT_DIR"

echo "Processing retrosheet game files..."

# Process each decade directory
for decade_dir in "$SRC_DIR"/*seve; do
    if [ -d "$decade_dir" ]; then
        decade=$(basename "$decade_dir" | sed 's/seve$//')
        echo "Processing decade: $decade"
        
        # Extract year from decade (e.g., 1910seve -> 1910)
        year_start="${decade:0:3}0"
        
        # Process each year in the decade
        for year in $(seq $year_start $((year_start + 9))); do
            # Check if year directory exists or files exist for this year
            evn_files=$(find "$decade_dir" -name "${year}*.EVN" | head -1)
            eva_files=$(find "$decade_dir" -name "${year}*.EVA" | head -1)
            
            if [ -n "$evn_files" ] || [ -n "$eva_files" ]; then
                echo "  Processing year: $year"
                
                # Process game files
                # -n: no header
                # -f 0-83: all fields
                # -y: year (helps find team file)
                output_file="$OUTPUT_DIR/games_${year}.csv"
                
                if [ -f "$output_file" ]; then
                    echo "    Skipping $year (output already exists)"
                    continue
                fi
                
                cd "$decade_dir"
                
                # Create team file symlink if TEAM file exists for this year
                team_file=$(find . -iname "TEAM${year}" -o -iname "team${year}" 2>/dev/null | head -1)
                if [ -n "$team_file" ] && [ ! -f "team" ]; then
                    ln -s "$team_file" "team" 2>/dev/null || cp "$team_file" "team" 2>/dev/null
                fi
                
                # Run cwgame and filter out version/help messages
                # Keep only lines that look like CSV data (contain quotes and commas)
                cwgame -n -f 0-83 -y "$year" "${year}"*.EV* 2>&1 | \
                    grep -E '^".*",' > "$PROJECT_ROOT/$output_file" || true
                
                # Clean up team symlink
                if [ -L "team" ]; then
                    rm -f "team"
                fi
                
                cd "$PROJECT_ROOT"
                
                if [ -s "$output_file" ]; then
                    echo "    Created: $output_file"
                else
                    echo "    Warning: $output_file is empty or failed"
                    rm -f "$output_file"
                fi
            fi
        done
    fi
done

echo "Game processing complete!"

