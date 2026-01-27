#!/bin/bash

# Script to process retrosheet event files using cwevent
# This processes all .EVN and .EVA files in the events directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

SRC_DIR="data/events"
OUTPUT_DIR="data/processed/events"
mkdir -p "$OUTPUT_DIR"

echo "Processing retrosheet event files..."

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
                
                # Process event files
                # -n: no header
                # -f 0-96: all fields
                # -y: year filter
                output_file="$OUTPUT_DIR/events_${year}.csv"
                
                if [ -f "$output_file" ]; then
                    echo "    Skipping $year (output already exists)"
                    continue
                fi
                
                cd "$decade_dir"
                cwevent -n -f 0-96 -y "$year" "${year}"*.EV* > "$PROJECT_ROOT/$output_file" 2>/dev/null
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

echo "Event processing complete!"

