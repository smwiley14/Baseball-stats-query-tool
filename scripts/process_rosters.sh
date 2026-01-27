#!/bin/bash

# Script to process retrosheet roster files
# Roster files (.ROS) are already in CSV format, so we just need to combine them
# Format: playerid,lastname,firstname,batting_hand,throwing_hand,team,position

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

EVENTS_DIR="data/events"
BOX_SCORES_DIR="data/box_scores"
OUTPUT_DIR="data/processed/rosters"
mkdir -p "$OUTPUT_DIR"

echo "Processing retrosheet roster files..."

# CSV header for roster files
ROSTER_HEADER="player_id,last_name,first_name,batting_hand,throwing_hand,team,position"

# Process event rosters
echo "Processing event rosters..."
for decade_dir in "$EVENTS_DIR"/*seve; do
    if [ -d "$decade_dir" ]; then
        decade=$(basename "$decade_dir" | sed 's/seve$//')
        echo "Processing decade: $decade"
        
        # Extract year from decade (e.g., 1910seve -> 1910)
        year_start="${decade:0:3}0"
        
        # Process each year in the decade
        for year in $(seq $year_start $((year_start + 9))); do
            ros_files=$(find "$decade_dir" -name "*${year}*.ROS" 2>/dev/null)
            
            if [ -n "$ros_files" ]; then
                echo "  Processing year: $year"
                
                output_file="$OUTPUT_DIR/rosters_${year}.csv"
                
                if [ -f "$output_file" ]; then
                    echo "    Skipping $year (output already exists)"
                    continue
                fi
                
                # Add header and combine all roster files for this year
                echo "$ROSTER_HEADER" > "$output_file"
                for ros_file in $ros_files; do
                    # Filter out empty lines and append to output
                    grep -v '^$' "$ros_file" >> "$output_file"
                done
                
                if [ -s "$output_file" ]; then
                    line_count=$(wc -l < "$output_file" | tr -d ' ')
                    echo "    Created: $output_file ($line_count lines)"
                else
                    echo "    Warning: $output_file is empty or failed"
                    rm -f "$output_file"
                fi
            fi
        done
    fi
done

# Process box score rosters (for earlier years)
echo "Processing box score rosters..."
for decade_dir in "$BOX_SCORES_DIR"/*box; do
    if [ -d "$decade_dir" ]; then
        decade=$(basename "$decade_dir" | sed 's/box$//')
        echo "Processing decade: $decade"
        
        # Extract year from decade (e.g., 1890sbox -> 1890)
        year_start="${decade:0:3}0"
        
        # Process each year in the decade
        for year in $(seq $year_start $((year_start + 9))); do
            ros_files=$(find "$decade_dir" -name "*${year}*.ROS" 2>/dev/null)
            
            if [ -n "$ros_files" ]; then
                echo "  Processing year: $year"
                
                output_file="$OUTPUT_DIR/rosters_${year}.csv"
                
                # Only process if file doesn't exist (events take precedence)
                if [ -f "$output_file" ]; then
                    echo "    Skipping $year (already processed from events)"
                    continue
                fi
                
                # Add header and combine all roster files for this year
                echo "$ROSTER_HEADER" > "$output_file"
                for ros_file in $ros_files; do
                    # Filter out empty lines and append to output
                    grep -v '^$' "$ros_file" >> "$output_file"
                done
                
                if [ -s "$output_file" ]; then
                    line_count=$(wc -l < "$output_file" | tr -d ' ')
                    echo "    Created: $output_file ($line_count lines)"
                else
                    echo "    Warning: $output_file is empty or failed"
                    rm -f "$output_file"
                fi
            fi
        done
    fi
done

echo "Roster processing complete!"

